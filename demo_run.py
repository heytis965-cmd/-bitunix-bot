import time
from api_client import BitunixAPI
from strategy import analyze, generate_signal
from datetime import datetime, timezone

api = BitunixAPI("", "", "https://fapi.bitunix.com")
balance = 10.0
position = None
leverage = 5

for cycle in range(5):
    resp = api._get("/api/v1/futures/market/kline", {"symbol": "BTCUSDT", "interval": "1m", "limit": "200"})
    klines = resp.get("data", [])
    if len(klines) < 60:
        time.sleep(3)
        continue
    price = float(klines[-1]["close"])
    a = analyze(klines)
    s = generate_signal(a)
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")

    equity = balance
    pos_info = "NONE"
    if position:
        side = position["side"]
        entry = position["entry"]
        margin = position["margin"]
        if side == "LONG":
            upnl = (price - entry) / entry * margin * leverage
        else:
            upnl = (entry - price) / entry * margin * leverage
        equity = balance + margin + upnl
        pos_info = f"{side} @ {entry:.0f} PnL:{upnl:+.2f}"
        hit_tp = (side == "LONG" and price >= position["tp"]) or (side == "SHORT" and price <= position["tp"])
        hit_sl = (side == "LONG" and price <= position["sl"]) or (side == "SHORT" and price >= position["sl"])
        if hit_tp:
            profit = margin * leverage * 0.025
            balance += margin + profit
            print(f"  [{now}] TP HIT! +${profit:.2f}")
            position = None
        elif hit_sl:
            loss = margin * leverage * 0.015
            balance += margin - loss
            print(f"  [{now}] SL HIT! -${loss:.2f}")
            position = None

    progress = min(equity / 100 * 100, 100)
    print(f"[{now}] ${price:.2f} | {a['trend']} RSI:{a['rsi']:.0f} | {s['signal']}({s['score']}) | Bal:${balance:.2f} Eq:${equity:.2f} | {pos_info}")

    if not position and s["signal"] in ("LONG", "SHORT"):
        margin = balance * 0.9
        tp = round(price * 1.025, 2) if s["signal"] == "LONG" else round(price * 0.975, 2)
        sl = round(price * 0.985, 2) if s["signal"] == "LONG" else round(price * 1.015, 2)
        position = {"side": s["signal"], "entry": price, "margin": margin, "tp": tp, "sl": sl}
        balance -= margin
        print(f"  -> OPEN {s['signal']} margin=${margin:.2f} TP:{tp} SL:{sl}")

    time.sleep(3)

if position:
    resp = api._get("/api/v1/futures/market/tickers", {"symbols": "BTCUSDT"})
    data = resp.get("data", [])
    if isinstance(data, list) and data:
        price = float(data[0]["lastPrice"])
    else:
        price = float(data.get("lastPrice", 0))
    side = position["side"]
    entry = position["entry"]
    margin = position["margin"]
    if side == "LONG":
        upnl = (price - entry) / entry * margin * leverage
    else:
        upnl = (entry - price) / entry * margin * leverage
    balance += margin + upnl
    print(f"\nForce close {side}: PnL ${upnl:+.2f}")

print(f"\n=== FINAL: ${balance:.2f} (started $10)")
