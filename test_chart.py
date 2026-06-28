import requests
r = requests.get('http://localhost:5000/chart?symbol=BTCUSDT&entry=64000&exit=63500&side=SHORT&reason=TP&time=12:00', timeout=15)
html = r.text

# Check for common issues
print("Has DOCTYPE:", "<!DOCTYPE" in html)
print("Has head:", "<head>" in html)
print("Has body:", "<body>" in html)
print("Has script:", "<script>" in html)
print("Has chart div:", 'id="chart"' in html)
print("Has createChart:", "createChart" in html)
print("Has setData:", "setData" in html)

# Find the script section
import re
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if 'createChart' in s:
        print(f"\nScript {i} (first 500 chars):")
        print(s[:500])
