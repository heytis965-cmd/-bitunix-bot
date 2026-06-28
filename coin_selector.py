import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("bitunix_bot")

MIN_ATR_PCT = 0.3
MAX_ATR_PCT = 8.0
SCAN_COOLDOWN_CYCLES = 4
ALL_SYMBOLS = [
    "1000BONKUSDT", "1000PEPEUSDT", "1000SHIBUSDT", "1INCHUSDT", "AAVEUSDT",
    "ADAUSDT", "ALGOUSDT", "ALICEUSDT", "ALTUSDT", "ANKRUSDT",
    "APTUSDT", "ARBUSDT", "ARKMUSDT", "ARKUSDT", "ARPAUSDT",
    "ATOMUSDT", "AUCTIONUSDT", "AVAXUSDT", "AXSUSDT", "BATUSDT",
    "BCHUSDT", "BLZUSDT", "BNBUSDT", "BOMEUSDT", "BRETTUSDT",
    "BTCUSDT", "C98USDT", "CAKEUSDT", "CELOUSDT", "CELRUSDT",
    "CFXUSDT", "CHZUSDT", "COMPUSDT", "COREUSDT", "CRVUSDT",
    "CTSIUSDT", "CVXUSDT", "DASHUSDT", "DOGEUSDT", "DOGSUSDT",
    "DOTUSDT", "DRIFTUSDT", "DYDXUSDT", "EGLDUSDT", "EIGENUSDT",
    "ENJUSDT", "ENSUSDT", "ETCUSDT", "ETHFIUSDT", "ETHUSDT",
    "FETUSDT", "FILUSDT", "FLOWUSDT", "FTMUSDT", "GALAUSDT",
    "GMTUSDT", "GRTUSDT", "HBARUSDT", "HFTUSDT", "HIGHUSDT",
    "HOTUSDT", "HYPEUSDT", "ICXUSDT", "IDUSDT", "IMXUSDT",
    "INJUSDT", "IOSTUSDT", "IOTAUSDT", "IOTXUSDT", "JUPUSDT",
    "KASUSDT", "KAVAUSDT", "KNCUSDT", "KSMUSDT", "LDOUSDT",
    "LINKUSDT", "LPTUSDT", "LTCUSDT", "MANAUSDT", "MANTAUSDT",
    "MASKUSDT", "MATICUSDT", "MEMEUSDT", "MEUSDT", "MEWUSDT",
    "MINAUSDT", "MKRUSDT", "MOODENGUSDT", "NEARUSDT", "NEOUSDT",
    "NOTUSDT", "OCEANUSDT", "ONDOUSDT", "ONEUSDT", "ONTUSDT",
    "OPUSDT", "ORBSUSDT", "ORDIUSDT", "PENDLEUSDT", "PNUTUSDT",
    "POPCATUSDT", "PYTHUSDT", "QNTUSDT", "QTUMUSDT", "RADUSDT",
    "RAREUSDT", "RAYUSDT", "RENDERUSDT", "RENUSDT", "RLCUSDT",
    "RNDRUSDT", "ROSEUSDT", "RUNEUSDT", "RVNUSDT", "SANDUSDT",
    "SEIUSDT", "SFPUSDT", "SKLUSDT", "SNXUSDT", "SOLUSDT",
    "SSVUSDT", "STEEMUSDT", "STGUSDT", "STORJUSDT", "STRKUSDT",
    "STXUSDT", "SUIUSDT", "SUPERUSDT", "SUSHIUSDT", "TAOUSDT",
    "THETAUSDT", "TIAUSDT", "TLMUSDT", "TNSRUSDT", "TONUSDT",
    "TRBUSDT", "TRUMPUSDT", "TRXUSDT", "TURBOUSDT", "TWTUSDT",
    "UMAUSDT", "UNIUSDT", "VETUSDT", "WAVESUSDT", "WAXPUSDT",
    "WIFUSDT", "WLDUSDT", "WOOUSDT", "XLMUSDT", "XMRUSDT",
    "XRPUSDT", "XTZUSDT", "XVSUSDT", "YFIUSDT", "YGGUSDT",
    "ZECUSDT", "ZENUSDT", "ZILUSDT", "ZKUSDT", "ZROUSDT",
    "ZRXUSDT", "1000RATSUSDT", "1000SATSUSDT", "ACTUSDT", "ALPINEUSDT",
    "API3USDT", "ARUSDT", "BANUSDT", "BONDUSDT", "BSVUSDT",
    "CATIUSDT", "CHILLGUYUSDT", "CKBUSDT", "COMBOUSDT", "COTIUSDT",
    "CTKUSDT", "CVCUSDT", "DARUSDT", "DEXEUSDT", "DIAUSDT",
    "DUSKUSDT", "DYMUSDT", "EDUUSDT", "FIDAUSDT", "GASUSDT",
    "GOATUSDT", "GTCUSDT", "HEIUSDT", "HIVEUSDT", "ILVUSDT",
    "IOUSDT", "JSTUSDT", "JTOUSDT", "KEYUSDT", "KLAYUSDT",
    "LITUSDT", "LOOMUSDT", "LSKUSDT", "LTOUSDT", "MBLUSDT",
    "MDXUSDT", "MLNUSDT", "MOVRUSDT", "MTLUSDT", "NMRUSDT",
    "OGUSDT", "PIXELUSDT", "PORTALUSDT", "POWRUSDT", "PROMUSDT",
    "PUNDIXUSDT", "SLPUSDT", "SPELLUSDT", "STEEMUSDT", "VTHOUSDT",
    "WUSDT", "XEMUSDT", "XVGUSDT",
]


class CoinSelector:
    def __init__(self, api):
        self.api = api
        self.cached_symbols = []
        self.last_scan_cycle = -999
        self.scan_results = {}

    def analyze_symbol(self, symbol):
        try:
            resp = self.api._get("/api/v1/futures/market/kline",
                                 {"symbol": symbol, "interval": "1h", "limit": "50"}, timeout=8)
            if resp.get("code") != 0:
                return None
            klines = resp.get("data", [])
            if len(klines) < 20:
                return None

            closes = [float(k["close"]) for k in klines]
            highs = [float(k["high"]) for k in klines]
            lows = [float(k["low"]) for k in klines]
            volumes = [float(k.get("quoteVol", k.get("baseVol", 0))) for k in klines]

            price = closes[-1]
            if price <= 0:
                return None

            vol_avg = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0

            trs = []
            for i in range(1, len(closes)):
                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
                trs.append(tr)
            atr_val = sum(trs[-14:]) / min(len(trs), 14) if trs else 0
            atr_pct = atr_val / price * 100 if price > 0 else 0

            chg_24h = 0
            if len(closes) >= 24:
                chg_24h = (closes[-1] - closes[-24]) / closes[-24] * 100

            return {
                "symbol": symbol, "price": price,
                "volume": vol_avg, "atr_pct": atr_pct,
                "chg_24h": chg_24h, "high": max(highs[-24:]), "low": min(lows[-24:]),
            }
        except Exception:
            return None

    def score_symbol(self, info):
        atr = info["atr_pct"]
        vol = info["volume"]

        if atr < MIN_ATR_PCT or atr > MAX_ATR_PCT:
            return -1

        score = 0
        vol_score = min(vol / 500_000, 5)
        score += vol_score

        if 0.5 <= atr <= 3.0:
            score += 3
        elif 3.0 < atr <= 5.0:
            score += 2
        else:
            score += 1

        if info["symbol"] in ("BTCUSDT", "ETHUSDT"):
            score += 1.5
        elif info["symbol"] in ("SOLUSDT", "BNBUSDT", "XRPUSDT"):
            score += 0.5

        return round(score, 2)

    def select_coins(self, current_cycle, max_coins=30):
        if current_cycle - self.last_scan_cycle < SCAN_COOLDOWN_CYCLES and self.cached_symbols:
            return self.cached_symbols[:max_coins]

        log.info(f"Scanning {len(ALL_SYMBOLS)} coins via kline...")
        t0 = time.time()
        scored = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(self.analyze_symbol, sym): sym for sym in ALL_SYMBOLS}
            for future in as_completed(futures):
                info = future.result()
                if info:
                    s = self.score_symbol(info)
                    if s > 0:
                        scored.append((info["symbol"], s, info))

        scored.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in scored[:max_coins]]
        self.cached_symbols = selected
        self.last_scan_cycle = current_cycle
        self.scan_results = {s[0]: s[2] for s in scored[:max_coins]}

        elapsed = time.time() - t0
        log.info(f"Scanned {len(scored)} coins in {elapsed:.0f}s, selected {len(selected)}: {', '.join(selected[:8])}...")
        return selected

    def get_coin_info(self, symbol):
        return self.scan_results.get(symbol)
