import math
import json
import os

STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

def load_stats():
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"wins": 0, "losses": 0, "total_pnl": 0, "best_trade": 0, "worst_trade": 0,
                "avg_win": 0, "avg_loss": 0, "patterns": {}, "threshold": 4}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception:
        pass

def ema(data, period):
    if len(data) < period: return []
    k = 2 / (period + 1)
    result = [sum(data[:period]) / period]
    for i in range(period, len(data)):
        result.append(data[i] * k + result[-1] * (1 - k))
    return result

def rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal: return 0, 0, 0
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    offset = slow - fast
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]
    if len(macd_line) < signal: return 0, 0, 0
    signal_line = ema(macd_line, signal)
    return macd_line[-1], signal_line[-1], macd_line[-1] - signal_line[-1]

def atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return 0
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    if len(trs) < period: return sum(trs) / len(trs) if trs else 0
    atr_val = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period - 1) + trs[i]) / period
    return atr_val

def supertrend(highs, lows, closes, period=10, mult=3):
    if len(closes) < period + 1: return None, None
    atr_val = atr(highs, lows, closes, period)
    hl2 = [(highs[i] + lows[i]) / 2 for i in range(len(closes))]
    upper = hl2[-1] + mult * atr_val
    lower = hl2[-1] - mult * atr_val
    return (lower, "UP") if closes[-1] > upper else (upper, "DOWN")

def bollinger_bands(closes, period=20, std_dev=2):
    if len(closes) < period: return None, None, None
    recent = closes[-period:]
    mid = sum(recent) / period
    variance = sum((x - mid) ** 2 for x in recent) / period
    std = math.sqrt(variance)
    return mid + std_dev * std, mid, mid - std_dev * std

def detect_pump_dump(closes, highs, lows, volumes, ps=5, pl=20):
    if len(closes) < pl: return {"pump": False, "dump": False, "pump_s": 0, "dump_s": 0, "vol_spike": 1, "momentum": 0}
    chg_s = (closes[-1] - closes[-ps]) / closes[-ps] * 100
    vol_avg = sum(volumes[-pl:]) / pl
    vol_now = volumes[-1] if volumes else 0
    vol_spike = vol_now / vol_avg if vol_avg > 0 else 1
    momentum = (closes[-1] - closes[-3]) / closes[-3] * 100 if len(closes) >= 3 else 0
    pump_s = 0
    dump_s = 0
    if chg_s > 0.8 and vol_spike > 1.3: pump_s = min(10, int(chg_s * vol_spike))
    if chg_s > 2.0 and vol_spike > 2.0: pump_s = min(10, int(chg_s * vol_spike * 0.5))
    if chg_s < -0.8 and vol_spike > 1.3: dump_s = min(10, int(abs(chg_s) * vol_spike))
    if chg_s < -2.0 and vol_spike > 2.0: dump_s = min(10, int(abs(chg_s) * vol_spike * 0.5))
    if momentum > 1.5 and pump_s > 0: pump_s = min(10, pump_s + 2)
    if momentum < -1.5 and dump_s > 0: dump_s = min(10, dump_s + 2)
    return {"pump": pump_s >= 3, "dump": dump_s >= 3, "pump_s": pump_s, "dump_s": dump_s,
            "vol_spike": vol_spike, "momentum": momentum, "chg_s": chg_s}

def analyze(klines):
    closes = [float(k["close"]) for k in klines]
    highs = [float(k["high"]) for k in klines]
    lows = [float(k["low"]) for k in klines]
    volumes = [float(k.get("quoteVol", k.get("baseVol", 0))) for k in klines]
    price = closes[-1]

    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200) if len(closes) >= 200 else []
    rsi_val = rsi(closes, 14)
    macd_val, signal_val, hist_val = macd(closes, 12, 26, 9)
    atr_val = atr(highs, lows, closes, 14)
    st_level, st_dir = supertrend(highs, lows, closes, 10, 3)
    bb_upper, bb_mid, bb_lower = bollinger_bands(closes, 20, 2)
    pd = detect_pump_dump(closes, highs, lows, volumes)

    vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1
    vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1

    long_trend = "NEUTRAL"
    if ema200: long_trend = "UP" if price > ema200[-1] else "DOWN"
    short_trend = "NEUTRAL"
    if ema9 and ema21 and ema50:
        if ema9[-1] > ema21[-1] > ema50[-1]: short_trend = "UP"
        elif ema9[-1] < ema21[-1] < ema50[-1]: short_trend = "DOWN"

    candle_score = 0
    if len(closes) >= 3:
        c1, c2 = closes[-1], closes[-2]
        o1 = float(klines[-1]["open"])
        if c1 > c2 and o1 < c2: candle_score += 1
        if c1 < c2 and o1 > c2: candle_score -= 1

    bb_position = 50
    if bb_upper and bb_lower and bb_upper != bb_lower:
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) * 100

    return {
        "price": price,
        "ema9": ema9[-1] if ema9 else price, "ema21": ema21[-1] if ema21 else price,
        "ema50": ema50[-1] if ema50 else price, "ema200": ema200[-1] if ema200 else price,
        "rsi": rsi_val,
        "macd": macd_val, "macd_signal": signal_val, "macd_hist": hist_val,
        "atr": atr_val, "atr_pct": atr_val / price * 100 if price > 0 else 0,
        "supertrend_dir": st_dir,
        "long_trend": long_trend, "short_trend": short_trend,
        "candle_score": candle_score, "vol_ratio": vol_ratio,
        "pump_dump": pd,
        "bb_upper": bb_upper, "bb_mid": bb_mid, "bb_lower": bb_lower,
        "bb_position": bb_position,
    }


def score_tf(analysis, direction):
    if not analysis: return 0
    s = 0
    if analysis["long_trend"] == direction: s += 2
    if analysis["short_trend"] == direction: s += 1
    if analysis["supertrend_dir"] == direction: s += 2
    if direction == "UP" and analysis["rsi"] < 40: s += 1
    elif direction == "DOWN" and analysis["rsi"] > 60: s += 1
    if direction == "UP" and analysis["ema9"] > analysis["ema21"]: s += 1
    elif direction == "DOWN" and analysis["ema9"] < analysis["ema21"]: s += 1
    if analysis.get("macd_hist", 0) > 0 and direction == "UP": s += 1
    elif analysis.get("macd_hist", 0) < 0 and direction == "DOWN": s += 1
    if analysis.get("bb_position", 50) < 30 and direction == "UP": s += 1
    elif analysis.get("bb_position", 50) > 70 and direction == "DOWN": s += 1
    if analysis.get("vol_ratio", 1) > 1.5: s += 1
    return s


def generate_signal(analysis):
    mtf = {"price": analysis["price"], "4h": None, "1h": analysis, "5m": analysis}
    return generate_signal_mtf(mtf)


def generate_signal_mtf(mtf):
    stats = load_stats()
    price = mtf["price"]
    a_4h = mtf.get("4h")
    a_1h = mtf["1h"]
    a_5m = mtf["5m"]

    pd = a_5m["pump_dump"] if a_5m else a_1h["pump_dump"]
    pd_score = 0
    if pd["dump"] and pd["dump_s"] >= 3:
        pd_score = -pd["dump_s"]
    elif pd["pump"] and pd["pump_s"] >= 3:
        pd_score = pd["pump_s"]

    score_4h = score_tf(a_4h, "UP") - score_tf(a_4h, "DOWN") if a_4h else (score_tf(a_1h, "UP") - score_tf(a_1h, "DOWN")) * 0.5
    score_1h = score_tf(a_1h, "UP") - score_tf(a_1h, "DOWN")
    score_5m = score_tf(a_5m, "UP") - score_tf(a_5m, "DOWN") if a_5m else 0

    raw_total = score_4h * 2 + score_1h * 1.5 + score_5m * 1 + pd_score * 1.5
    direction = "UP" if raw_total > 0 else "DOWN"
    if abs(raw_total) < 0.5:
        return {"signal": "HOLD", "score": 0, "reasons": ["No clear direction"], "analysis": a_5m or a_1h, "confirmations": 0, "mtf": {"4h": score_4h, "1h": score_1h, "5m": score_5m}}

    confirmations = 0
    reasons = []

    if (score_4h > 0 and direction == "UP") or (score_4h < 0 and direction == "DOWN"):
        confirmations += 1; reasons.append(f"4H:{score_4h}")
    if (score_1h > 0 and direction == "UP") or (score_1h < 0 and direction == "DOWN"):
        confirmations += 1; reasons.append(f"1H:{score_1h}")
    if (score_5m > 0 and direction == "UP") or (score_5m < 0 and direction == "DOWN"):
        confirmations += 1; reasons.append(f"5M:{score_5m}")

    if pd["dump"] and direction == "DOWN":
        confirmations += 1; reasons.append(f"Dump")
    elif pd["pump"] and direction == "UP":
        confirmations += 1; reasons.append(f"Pump")

    a15 = a_5m or a_1h
    if a15:
        if a15["supertrend_dir"] == direction: confirmations += 1; reasons.append("ST")
        if a15["vol_ratio"] > 1.5: confirmations += 1; reasons.append(f"Vol:{a15['vol_ratio']:.1f}")
        if a15["candle_score"] != 0 and ((a15["candle_score"] > 0 and direction == "UP") or (a15["candle_score"] < 0 and direction == "DOWN")):
            confirmations += 1; reasons.append("Candle")
        bb = a15.get("bb_position", 50)
        if direction == "UP" and bb < 30: confirmations += 1; reasons.append("BB_low")
        elif direction == "DOWN" and bb > 70: confirmations += 1; reasons.append("BB_high")

    threshold = stats.get("threshold", 4)

    abs_score = abs(int(raw_total))
    signal = "HOLD"
    if abs_score >= threshold and direction == "UP" and confirmations >= 4:
        signal = "LONG"
    elif abs_score >= threshold and direction == "DOWN" and confirmations >= 4:
        signal = "SHORT"

    combined = (a_5m or a_1h or {}).copy()
    combined["long_trend"] = direction

    return {
        "signal": signal, "score": abs_score, "threshold": threshold,
        "confirmations": confirmations, "reasons": reasons,
        "analysis": combined, "mtf": {"4h": score_4h, "1h": score_1h, "5m": score_5m},
    }
