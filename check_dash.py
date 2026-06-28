import requests, json

r = requests.get('http://localhost:5000', timeout=5)
html = r.text

state = json.load(open("bot_state.json"))

print("=== DASHBOARD vs STATE ===")
print(f"Balance in HTML: {'$13.53' in html or '$13.5' in html}")
print(f"Equity in HTML: {'$26' in html or '$27' in html}")
print(f"Positions count in HTML: {'1000BONKUSDT' in html}")
print(f"Session start in HTML: {'Session Start' in html}")

# Check calendar rendering
if 'cal-day' in html:
    import re
    cal_days = re.findall(r'cal-day[^"]*"', html)
    print(f"\nCalendar cells rendered: {len(cal_days)}")

# Check for any error messages
import re
errors = re.findall(r'(\d{3} Error)', html)
print(f"HTTP errors in page: {errors}")

# Check all sections visible
sections = ['Account', 'Performance', 'AI Model', 'Daily Risk', 'PnL Calendar', 'Open Positions', 'Top Signals']
for s in sections:
    count = html.count(s)
    print(f"Section '{s}': appears {count}x")
