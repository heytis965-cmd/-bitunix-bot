import json
import os
import requests
from api_client import BitunixAPI

# Download the library content
LIB_PATH = os.path.join(os.path.dirname(__file__), "static", "lightweight-charts.js")
if not os.path.exists(LIB_PATH):
    os.makedirs(os.path.dirname(LIB_PATH), exist_ok=True)
    r = requests.get("https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js", timeout=15)
    with open(LIB_PATH, "wb") as f:
        f.write(r.content)
    print(f"Downloaded library: {len(r.content)} bytes")

# Test chart generation
api = BitunixAPI("", "", "https://fapi.bitunix.com")
resp = api._get("/api/v1/futures/market/kline", {"symbol": "BTCUSDT", "interval": "5m", "limit": "50"}, timeout=15)
data = resp.get("data", []) if resp.get("code") == 0 else []
print(f"Klines: {len(data)} candles")

if data:
    candles = json.dumps([{"time": int(k["time"]) // 1000, "open": float(k["open"]), "high": float(k["high"]), "low": float(k["low"]), "close": float(k["close"])} for k in data])
    
    with open(LIB_PATH, "r", encoding="utf-8") as f:
        lib_js = f.read()
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>BTCUSDT Chart</title>
<style>body{{margin:0;background:#0a0a1a}}#chart{{width:100%;height:600px}}</style></head>
<body><div id="chart"></div>
<script>{lib_js}</script>
<script>
var chart = LightweightCharts.createChart(document.getElementById('chart'),{{
    layout:{{background:{{color:'#0a0a1a'}},textStyle:{{color:'#e0e0e0'}}}},
    grid:{{vertLines:{{color:'#1e1e3a'}},horzLines:{{color:'#1e1e3a'}}}},
    crosshair:{{mode:0}},timeScale:{{timeVisible:true,secondsVisible:false}}
}});
var series = chart.addCandlestickSeries({{upColor:'#00ff88',downColor:'#ff4466'}});
series.setData({candles});
chart.timeScale().fitContent();
series.createPriceLine({{price:64000,color:'#ff4466',lineWidth:2,lineStyle:2,title:'Entry'}});
series.createPriceLine({{price:63500,color:'#00ff88',lineWidth:2,lineStyle:1,title:'Exit'}});
</script></body></html>"""
    
    with open("chart_test.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved chart_test.html: {len(html)} bytes")
    print("Open this file in browser to test")
