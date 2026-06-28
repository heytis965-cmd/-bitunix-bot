from api_client import BitunixAPI
import json

api = BitunixAPI("", "", "https://fapi.bitunix.com")

for ep in ["/api/v1/futures/market/symbols", "/api/v1/futures/public/symbol", "/api/v1/futures/market/contracts"]:
    r = api._get(ep, timeout=15)
    data = r.get("data", [])
    print(f"\n=== {ep} ===")
    print(f"code: {r.get('code')}, type: {type(data).__name__}, len: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
    if isinstance(data, list) and data:
        print("First item keys:", list(data[0].keys()) if isinstance(data[0], dict) else data[0])
        print("First 3:", json.dumps(data[:3], indent=2)[:500])
    elif isinstance(data, dict):
        print("Keys:", list(data.keys())[:10])
        first_val = list(data.values())[0] if data else None
        if first_val:
            print("First value:", json.dumps(first_val, indent=2)[:300])
