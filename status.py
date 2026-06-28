import json
with open(r"C:\Users\Леонид\Mimo_Projects\bitunix_bot\bot_state.json") as f:
    s = json.load(f)
eq = s["balance"] + sum(p["margin"] + p.get("unrealized", 0) for p in s["positions"])
print(f"Balance: ${s['balance']:.2f}")
print(f"Equity: ${eq:.2f}")
print(f"Trades: {s['total_trades']} (W:{s['wins']} L:{s['losses']})")
print(f"Open positions: {len(s['positions'])}")
for p in s["positions"]:
    print(f"  {p['side']} {p['symbol']} unrealized=${p.get('unrealized',0):+.2f}")
print(f"Cycle: #{s['cycle_count']}")
print(f"Start: $25 -> Now: ${eq:.2f} ({(eq-25)/25*100:+.1f}%)")
