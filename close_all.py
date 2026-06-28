from api_client import BitunixAPI
from config import API_KEY, API_SECRET, BASE_URL

api = BitunixAPI(API_KEY, API_SECRET, BASE_URL)

symbols = ["BTCUSDT", "XRPUSDT", "DOGEUSDT"]
for sym in symbols:
    r = api.flash_close_position(sym)
    print(f"Close {sym}: {r}")

r = api.get_account("USDT")
print(f"\nAccount: {r}")
