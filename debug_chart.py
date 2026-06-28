import requests, json, re
from datetime import datetime, timezone, timedelta

r = requests.get('http://127.0.0.1:5000/chart?symbol=ALICEUSDT&entry=0.11399&exit=0.116614&side=SHORT&reason=SL&open_time=11:08&close_time=11:08', timeout=15)
html = r.text
m = re.search(r'var data=(\[.*?\]);', html)
data = json.loads(m.group(1))
print(f'Candles: {len(data)}')

tz5 = timezone(timedelta(hours=5))
first = datetime.fromtimestamp(data[0]['time'], tz=tz5)
last = datetime.fromtimestamp(data[-1]['time'], tz=tz5)
print(f'Range: {first.strftime("%H:%M")} - {last.strftime("%H:%M")} (UTC+5)')

entry = 0.11399
exit_p = 0.116614
print(f'\nEntry: {entry} | Exit: {exit_p}')
for i,d in enumerate(data):
    dt = datetime.fromtimestamp(d['time'], tz=tz5)
    if d['low'] <= entry <= d['high']:
        print(f'  ENTRY candle: {dt.strftime("%H:%M")} L={d["low"]} H={d["high"]}')
    if d['low'] <= exit_p <= d['high']:
        print(f'  EXIT candle:  {dt.strftime("%H:%M")} L={d["low"]} H={d["high"]}')
