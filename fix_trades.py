import json
trades = json.load(open("trades_log.json", encoding="utf-8"))
for t in trades:
    if t["reason"] == "SL" and t["pnl"] > 0:
        print(f"Fixing: {t['symbol']} SL with pnl={t['pnl']} -> TP")
        t["reason"] = "TP"
trades = [t for t in trades if not (t["reason"] == "SL" and t["pnl"] > 0)]
json.dump(trades, open("trades_log.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"Total trades: {len(trades)}")
