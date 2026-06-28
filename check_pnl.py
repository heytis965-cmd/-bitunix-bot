import json
d = json.load(open("pnl_history.json"))
b = json.load(open("bot_state.json"))
pos = b["positions"]
margin = sum(p["margin"] for p in pos)
unrl = sum(p["unrealized"] for p in pos)
eq = b["balance"] + margin + unrl
start = d["2026-06-23"]["start_equity"]
print(f"Balance: ${b['balance']:.2f}")
print(f"Margin: ${margin:.2f}")
print(f"Unrealized: ${unrl:.2f}")
print(f"Equity: ${eq:.2f}")
print(f"Start: ${start}")
print(f"Real PnL: ${eq - start:.2f}")
print(f"Recorded PnL: ${d['2026-06-23']['pnl_usd']}")
