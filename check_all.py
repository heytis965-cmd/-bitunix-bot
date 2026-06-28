import json
trades = json.load(open("trades_log.json", encoding="utf-8"))
print(f"Total: {len(trades)}")
for i, t in enumerate(trades):
    print(f"  {i+1}. [{t['date']}] {t['time']} {t['symbol']:14} {t['reason']:10} {t['pnl']:+.2f}$")
