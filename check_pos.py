from api_client import BitunixAPI
from config import API_KEY, API_SECRET, BASE_URL
api = BitunixAPI(API_KEY, API_SECRET, BASE_URL)

r = api.get_positions()
positions = r.get("data", [])
if not isinstance(positions, list):
    positions = [positions] if positions else []
print("=== POSITIONS ===")
for p in positions:
    if float(p.get("qty", 0)) > 0:
        print(f"{p['symbol']} | {p['side']} | Entry: {p['avgOpenPrice']} | PnL: {p.get('unrealizedPNL', 0)} | Qty: {p.get('qty')}")

r2 = api.get_account("USDT")
acc = r2.get("data", {})
if isinstance(acc, list):
    acc = acc[0] if acc else {}
print(f"\n=== ACCOUNT ===")
print(f"Available: ${acc.get('available', 0)} | Margin: ${acc.get('margin', 0)} | Unrealized: ${acc.get('crossUnrealizedPNL', 0)}")
