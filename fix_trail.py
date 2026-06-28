import json
trades = json.load(open("trades_log.json", encoding="utf-8"))
for t in trades:
    if t["reason"] == "SL" and t["pnl"] > 0:
        t["reason"] = "Trail"
        print(f"Fixed: {t['symbol']} SL -> Trail (pnl={t['pnl']})")
json.dump(trades, open("trades_log.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"Total: {len(trades)}")
