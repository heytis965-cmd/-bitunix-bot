import json
from pnl_tracker import update_today_pnl, load_pnl

# Test: manually call update_today_pnl with known values
update_today_pnl(262.84, 318.21, 47, 45, 2)
pnl = load_pnl()
print("pnl_history after update:", json.dumps(pnl.get("2026-06-23", {}), indent=2))
