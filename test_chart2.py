import requests
r = requests.get('http://localhost:5000/chart?symbol=BTCUSDT&entry=64000&exit=63500&side=SHORT&reason=TP&time=12:00', timeout=15)
html = r.text

# Check if data is empty
import re
data_match = re.search(r'var data5m = (\[.*?\]);', html, re.DOTALL)
if data_match:
    data = data_match.group(1)
    print(f"Data length: {len(data)}")
    print(f"First 200 chars: {data[:200]}")
else:
    print("No data found!")
    # Find the script section
    scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
    for i, s in enumerate(scripts):
        if 'setData' in s:
            # Find the data line
            for line in s.split('\n'):
                if 'data5m' in line and '=' in line:
                    print(f"Line: {line.strip()[:200]}")
