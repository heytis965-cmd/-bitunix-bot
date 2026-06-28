import sys
import time
import logging
from datetime import datetime, timezone

from config import (
    API_KEY, API_SECRET, BASE_URL, LEVERAGE, MARGIN_COIN, SYMBOL,
    KLINE_INTERVAL, KLINE_LIMIT, POSITION_SIZE_PCT, STOP_LOSS_PCT,
    TAKE_PROFIT_PCT, EMA_FAST, EMA_SLOW, RSI_PERIOD, RSI_OVERBOUGHT,
    RSI_OVERSOLD, VOLUME_MULT, SCAN_INTERVAL_SEC, LOG_FILE,
)
from api_client import BitunixAPI
from strategy import analyze, generate_signal
import os


def setup_keys():
    global API_KEY, API_SECRET
    if API_KEY != "YOUR_API_KEY_HERE" and API_SECRET != "YOUR_API_SECRET_HERE":
        return
    print("=" * 50)
    print("  FIRST RUN - Enter your Bitunix API keys")
    print("=" * 50)
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    if not api_key or not api_secret:
        print("Keys cannot be empty!")
        sys.exit(1)
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace('API_KEY = "YOUR_API_KEY_HERE"', f'API_KEY = "{api_key}"')
    content = content.replace('API_SECRET = "YOUR_API_SECRET_HERE"', f'API_SECRET = "{api_secret}"')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    API_KEY = api_key
    API_SECRET = api_secret
    print("Keys saved!\n")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("bitunix_bot")


class TradingBot:
    def __init__(self):
        self.api = BitunixAPI(API_KEY, API_SECRET, BASE_URL)
        self.symbol = SYMBOL
        self.running = True
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.start_balance = 0
        self.current_position = None

    def print_banner(self):
        print("=" * 60)
        print("  BITUNIX FUTURES TRADING BOT")
        print(f"  Symbol: {self.symbol}")
        print(f"  Leverage: {LEVERAGE}x")
        print(f"  Start: $25 -> Target: $500")
        print("=" * 60)

    def _parse_account(self, resp):
        if resp.get("code") != 0:
            return None
        data = resp.get("data")
        if not data:
            return None
        if isinstance(data, list):
            return data[0] if data else None
        return data

    def check_connection(self):
        log.info("Checking API connection...")
        resp = self.api.get_account(MARGIN_COIN)
        acc = self._parse_account(resp)
        if not acc:
            log.error(f"API connection failed: {resp}")
            return False
        balance = float(acc.get("available", 0))
        margin = float(acc.get("margin", 0))
        total = balance + margin
        log.info(
            f"Account OK | Available: ${balance:.2f} | Margin: ${margin:.2f} | "
            f"Total: ${total:.2f} | Mode: {acc.get('positionMode', '?')}"
        )
        self.start_balance = total
        return True

    def get_balance(self):
        resp = self.api.get_account(MARGIN_COIN)
        acc = self._parse_account(resp)
        if not acc:
            return 0, 0
        return float(acc.get("available", 0)), float(acc.get("margin", 0))

    def set_leverage(self):
        log.info(f"Setting leverage to {LEVERAGE}x for {self.symbol}...")
        resp = self.api.change_leverage(self.symbol, LEVERAGE, MARGIN_COIN)
        if resp.get("code") == 0:
            log.info("Leverage set OK")
        else:
            log.warning(f"Set leverage response: {resp}")

    def get_klines(self):
        resp = self.api.get_kline(self.symbol, KLINE_INTERVAL, KLINE_LIMIT)
        if resp.get("code") != 0:
            log.error(f"Failed to get klines: {resp}")
            return []
        return resp.get("data", [])

    def get_positions(self):
        resp = self.api.get_positions(self.symbol)
        if resp.get("code") != 0:
            return []
        data = resp.get("data", [])
        if isinstance(data, dict):
            data = [data]
        return [p for p in data if float(p.get("qty", 0)) > 0]

    def calc_position_size(self, available, price):
        margin = available * POSITION_SIZE_PCT
        size_usd = margin * LEVERAGE
        qty = size_usd / price
        return round(qty, 6)

    def open_long(self, price, qty):
        tp = round(price * (1 + TAKE_PROFIT_PCT), 2)
        sl = round(price * (1 - STOP_LOSS_PCT), 2)
        log.info(
            f"OPENING LONG | Qty: {qty} | Entry: ~{price} | "
            f"TP: {tp} | SL: {sl}"
        )
        resp = self.api.place_order(
            symbol=self.symbol,
            side="BUY",
            trade_side="OPEN",
            order_type="MARKET",
            qty=qty,
            tp_price=tp,
            sl_price=sl,
        )
        log.info(f"Long order response: {resp}")
        return resp.get("code") == 0

    def open_short(self, price, qty):
        tp = round(price * (1 - TAKE_PROFIT_PCT), 2)
        sl = round(price * (1 + STOP_LOSS_PCT), 2)
        log.info(
            f"OPENING SHORT | Qty: {qty} | Entry: ~{price} | "
            f"TP: {tp} | SL: {sl}"
        )
        resp = self.api.place_order(
            symbol=self.symbol,
            side="SELL",
            trade_side="OPEN",
            order_type="MARKET",
            qty=qty,
            tp_price=tp,
            sl_price=sl,
        )
        log.info(f"Short order response: {resp}")
        return resp.get("code") == 0

    def close_all(self):
        log.info("Closing all positions...")
        resp = self.api.flash_close_position(self.symbol)
        log.info(f"Close response: {resp}")
        return resp.get("code") == 0

    def print_status(self, analysis, signal_result, balance, margin):
        now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        total = balance + margin
        pnl_pct = ((total - self.start_balance) / self.start_balance * 100) if self.start_balance else 0

        print(f"\n[{now}] {self.symbol} ${analysis['price']:.2f}")
        print(f"  Balance: ${balance:.2f} | Margin: ${margin:.2f} | "
              f"Total: ${total:.2f} | PnL: {pnl_pct:+.1f}%")
        print(f"  Trend: {analysis['long_trend']} | RSI: {analysis['rsi']:.1f} | "
              f"MACD: {analysis['macd_hist']:.2f} | Vol: {analysis['vol_ratio']:.1f}x")
        print(f"  EMA9: {analysis['ema9']:.2f} | EMA21: {analysis['ema21']:.2f} | "
              f"EMA50: {analysis['ema50']:.2f}")
        print(f"  Signal: {signal_result['signal']} (score: {signal_result['score']})")
        if signal_result["reasons"]:
            print(f"  Reasons: {', '.join(signal_result['reasons'][:3])}")
        print(f"  Trades: {self.total_trades} | "
              f"Win rate: {self.wins/self.total_trades*100:.0f}%" if self.total_trades else "")
        print("-" * 55)

    def check_target(self, balance, margin):
        total = balance + margin
        if total >= 500:
            log.info(f"*** TARGET REACHED! Balance: ${total:.2f} ***")
            return True
        if total < 1:
            log.warning(f"*** LOW BALANCE: ${total:.2f} - stopping ***")
            return True
        return False

    def run_cycle(self):
        klines = self.get_klines()
        if len(klines) < 60:
            log.warning("Not enough kline data")
            return

        analysis = analyze(klines)
        signal_result = generate_signal(analysis)

        balance, margin = self.get_balance()
        total = balance + margin

        if self.check_target(balance, margin):
            self.running = False
            return

        self.print_status(analysis, signal_result, balance, margin)

        positions = self.get_positions()
        has_position = len(positions) > 0

        if has_position:
            pos = positions[0]
            side = pos.get("side", "")
            entry = float(pos.get("avgOpenPrice", 0))
            unrealized = float(pos.get("unrealizedPNL", 0))

            if signal_result["signal"] == "HOLD":
                return

            should_close = False
            if side == "LONG" and signal_result["signal"] == "SHORT":
                should_close = True
                reason = "Signal flipped to SHORT"
            elif side == "SHORT" and signal_result["signal"] == "LONG":
                should_close = True
                reason = "Signal flipped to LONG"
            elif side == "LONG" and signal_result["score"] <= -3:
                should_close = True
                reason = "Strong bearish signal"
            elif side == "SHORT" and signal_result["score"] >= 3:
                should_close = True
                reason = "Strong bullish signal"

            if should_close:
                log.info(f"Closing {side} - {reason}")
                self.close_all()
                self.total_trades += 1
                if unrealized > 0:
                    self.wins += 1
                else:
                    self.losses += 1
                time.sleep(1)

        if not has_position and signal_result["signal"] != "HOLD":
            available, _ = self.get_balance()
            if available < 1:
                log.warning("Insufficient balance to open position")
                return

            qty = self.calc_position_size(available, analysis["price"])
            if qty <= 0:
                return

            if signal_result["signal"] == "LONG":
                success = self.open_long(analysis["price"], qty)
            elif signal_result["signal"] == "SHORT":
                success = self.open_short(analysis["price"], qty)
            else:
                return

            if success:
                self.total_trades += 1

    def run(self):
        setup_keys()
        self.print_banner()

        if not self.check_connection():
            log.error("Cannot connect to API. Check your keys.")
            return

        self.set_leverage()

        log.info("Starting main loop... (Ctrl+C to stop)")
        while self.running:
            try:
                self.run_cycle()
                time.sleep(SCAN_INTERVAL_SEC)
            except KeyboardInterrupt:
                log.info("Stopped by user")
                self.running = False
            except Exception as e:
                log.error(f"Error in cycle: {e}", exc_info=True)
                time.sleep(5)

        balance, margin = self.get_balance()
        total = balance + margin
        log.info(
            f"Bot stopped. Final: ${total:.2f} | "
            f"Trades: {self.total_trades} | "
            f"Win rate: {self.wins/self.total_trades*100:.0f}%"
            if self.total_trades
            else f"Bot stopped. Final: ${total:.2f} | No trades"
        )


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
