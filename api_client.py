import hashlib
import hmac
import json
import time
import random
import string
import requests


class BitunixAPI:
    def __init__(self, api_key, api_secret, base_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def _nonce(self):
        return "".join(random.choices(string.ascii_letters + string.digits, k=32))

    def _timestamp(self):
        return str(int(time.time() * 1000))

    def _sign(self, nonce, timestamp, query_params, body_str):
        digest_input = nonce + timestamp + self.api_key + query_params + body_str
        digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
        sign_input = digest + self.api_secret
        return hashlib.sha256(sign_input.encode("utf-8")).hexdigest()

    def _headers(self, sign, nonce, timestamp):
        return {
            "api-key": self.api_key,
            "sign": sign,
            "nonce": nonce,
            "timestamp": timestamp,
            "Content-Type": "application/json",
            "language": "en-US",
        }

    def _get(self, path, params=None, timeout=10):
        nonce = self._nonce()
        ts = self._timestamp()
        query = ""
        if params:
            sorted_items = sorted(params.items())
            query = "".join(f"{k}{v}" for k, v in sorted_items)
        sign = self._sign(nonce, ts, query, "")
        url = self.base_url + path
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=self._headers(sign, nonce, ts), timeout=timeout)
                return resp.json()
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 2:
                    return {"code": -1, "msg": "Connection failed after retries"}
                time.sleep(1)

    def _post(self, path, data=None):
        nonce = self._nonce()
        ts = self._timestamp()
        body_str = json.dumps(data, separators=(",", ":")) if data else ""
        sign = self._sign(nonce, ts, "", body_str)
        for attempt in range(3):
            try:
                resp = requests.post(
                    self.base_url + path,
                    headers=self._headers(sign, nonce, ts),
                    data=body_str,
                    timeout=10,
                )
                return resp.json()
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 2:
                    return {"code": -1, "msg": "Connection failed after retries"}
                time.sleep(1)

    def get_account(self, margin_coin="USDT"):
        return self._get("/api/v1/futures/account", {"marginCoin": margin_coin})

    def get_tickers(self, symbols=None):
        params = {}
        if symbols:
            params["symbols"] = symbols
        return self._get("/api/v1/futures/market/tickers", params or None)

    def get_kline(self, symbol, interval="1m", limit=200):
        return self._get(
            "/api/v1/futures/market/kline",
            {"symbol": symbol, "interval": interval, "limit": str(limit)},
        )

    def get_positions(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/api/v1/futures/position/get_pending_positions", params or None)

    def change_leverage(self, symbol, leverage, margin_coin="USDT"):
        return self._post(
            "/api/v1/futures/account/change_leverage",
            {"symbol": symbol, "leverage": leverage, "marginCoin": margin_coin},
        )

    def place_order(
        self,
        symbol,
        side,
        trade_side,
        order_type,
        qty,
        price=None,
        effect="GTC",
        tp_price=None,
        sl_price=None,
    ):
        order = {
            "symbol": symbol,
            "side": side,
            "tradeSide": trade_side,
            "orderType": order_type,
            "qty": str(qty),
            "effect": effect,
        }
        if price and order_type == "LIMIT":
            order["price"] = str(price)
        if tp_price:
            order["tpPrice"] = str(tp_price)
            order["tpStopType"] = "MARK_PRICE"
            order["tpOrderType"] = "MARKET"
        if sl_price:
            order["slPrice"] = str(sl_price)
            order["slStopType"] = "MARK_PRICE"
            order["slOrderType"] = "MARKET"
        return self._post("/api/v1/futures/trade/place_order", order)

    def close_position(self, symbol, position_id):
        return self.place_order(
            symbol=symbol,
            side="SELL",
            trade_side="CLOSE",
            order_type="MARKET",
            qty="0",
            price="0",
        )

    def flash_close_position(self, symbol):
        return self._post(
            "/api/v1/futures/trade/flash_close_position",
            {"symbol": symbol},
        )
