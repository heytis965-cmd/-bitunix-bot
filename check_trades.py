import json
trades = json.load(open("trades_log.json"))
print(f"Total trades: {len(trades)}")
for t in trades[-8:]:
    pnl_sign = "+" if t["pnl"] >= 0 else ""
    print(f"  {t['time']} | {t['side']:5} {t['symbol']:14} | Margin: ${t['margin']:.2f} | PnL: {pnl_sign}${t['pnl']:.2f} | {t['reason']}")
