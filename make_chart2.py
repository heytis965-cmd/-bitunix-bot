import json
import os
import requests
from api_client import BitunixAPI

# Test the chart function directly
symbol = "BTCUSDT"
entry = 64000.0
exit_p = 63500.0
side = "SHORT"
reason = "TP"
trade_time = "12:00"

api = BitunixAPI("", "", "https://fapi.bitunix.com")
klines_5m = api._get("/api/v1/futures/market/kline", {"symbol": symbol, "interval": "5m", "limit": "50"}, timeout=15)
data_5m = klines_5m.get("data", []) if klines_5m.get("code") == 0 else []
candles_5m = json.dumps([{"time": int(k["time"]) // 1000, "open": float(k["open"]), "high": float(k["high"]), "low": float(k["low"]), "close": float(k["close"])} for k in data_5m])

badge_class = "badge-long" if side=="LONG" else "badge-short"
entry_label = "SHORT Entry" if side=="SHORT" else "LONG Entry"
exit_label = "SHORT Exit" if side=="SHORT" else "LONG Exit"

html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{symbol} - {reason}</title>
<style>body{{margin:0;background:#0a0a1a;color:#e0e0e0;font-family:sans-serif;overflow:hidden}}
.info{{padding:10px 15px;background:#12122a;border-bottom:1px solid #1e1e3a;font-size:13px;display:flex;gap:15px;align-items:center;flex-wrap:wrap}}
.info span{{color:#888}}.info b{{color:#e0e0e0}}
.badge{{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}}
.badge-long{{background:#00ff8822;color:#00ff88}}.badge-short{{background:#ff446622;color:#ff4466}}
canvas{{display:block;cursor:crosshair}}
.tooltip{{position:fixed;background:#1a1a2e;border:1px solid #333;padding:8px 12px;border-radius:6px;font-size:12px;pointer-events:none;display:none;z-index:100}}
.help{{position:fixed;bottom:10px;right:15px;color:#555;font-size:11px}}</style></head><body>
<div class="info"><b style="font-size:16px">{symbol}</b><span class="badge {badge_class}">{side}</span><span>{trade_time}</span>
<span>Entry: <b style="color:#ff4466">${entry:.6f}</b></span><span>Exit: <b style="color:#00ff88">${exit_p:.6f}</b></span><span>Reason: <b>{reason}</b></span></div>
<div class="tooltip" id="tip"></div>
<canvas id="c"></canvas>
<div class="help">Scroll: zoom | Drag: pan | Hover: price/time</div>
<script>
var data = {candles_5m};
var entry = {entry};
var exit_p = {exit_p};
var side = '{side}';
var c = document.getElementById('c');
var ctx = c.getContext('2d');
var tip = document.getElementById('tip');
var offset = 0;
var scale = 1;
var dragX = null;
var W, H, cw, ph, mn, mx;

function calcBounds(){{
    var all = [];
    var si = Math.max(0, Math.floor(-offset/scale));
    var ei = Math.min(data.length, Math.ceil((W-offset)/scale));
    for(var i=si;i<ei;i++){{all.push(data[i].low,data[i].high)}}
    all.push(entry,exit_p);
    mn = Math.min.apply(null,all);
    mx = Math.max.apply(null,all);
    var pad = (mx-mn)*0.12;
    mn -= pad; mx += pad;
    cw = Math.max(1, scale);
    ph = H/(mx-mn);
}}

function priceY(p){{return H-(p-mn)*ph;}}
function draw(){{
    c.width = window.innerWidth;
    c.height = window.innerHeight - 50;
    W = c.width; H = c.height;
    ctx.fillStyle = '#0a0a1a';
    ctx.fillRect(0,0,W,H);
    if(!data.length) return;
    calcBounds();
    ctx.fillStyle = '#222';
    ctx.fillRect(0,H-25,W,25);
    var si = Math.max(0, Math.floor(-offset/cw));
    var ei = Math.min(data.length, Math.ceil((W-offset)/cw));
    for(var i=si;i<ei;i++){{
        var d = data[i];
        var x = offset + i*cw;
        var o = H-(d.open-mn)*ph;
        var cl = H-(d.close-mn)*ph;
        var hi = H-(d.high-mn)*ph;
        var lo = H-(d.low-mn)*ph;
        var green = d.close>=d.open;
        var color = green?'#00ff88':'#ff4466';
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, cw*0.08);
        ctx.beginPath();ctx.moveTo(x+cw/2,hi);ctx.lineTo(x+cw/2,lo);ctx.stroke();
        ctx.fillStyle = color;
        ctx.fillRect(x+cw*0.15,Math.min(o,cl),cw*0.7,Math.max(1,Math.abs(cl-o)));
    }}
    function drawLine(p,color,label,dash){{
        var y = priceY(p);
        ctx.setLineDash(dash||[6,4]);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y-25);ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = color;
        ctx.font = 'bold 11px sans-serif';
        ctx.fillText(label+' $'+p.toFixed(6),W-200,y-8);
        ctx.beginPath();ctx.arc(W-210,y,4,0,Math.PI*2);ctx.fill();
    }}
    drawLine(entry,'#ff4466','{entry_label}');
    drawLine(exit_p,'#00ff88','{exit_label}',[]);
    var midI = Math.floor(data.length/2);
    var midX = offset + midI*cw;
    var midY = priceY(data[midI].close);
    ctx.beginPath();ctx.arc(midX,midY,5,0,Math.PI*2);
    ctx.fillStyle='#ffaa00';ctx.fill();
    ctx.font='10px sans-serif';ctx.fillStyle='#ffaa00';
    ctx.fillText(side,midX+8,midY-8);
    var si2=Math.max(0,Math.floor(-offset/cw));
    var ei2=Math.min(data.length,Math.ceil((W-offset)/cw));
    var step=Math.max(1,Math.floor((ei2-si2)/8));
    ctx.fillStyle='#666';ctx.font='10px sans-serif';
    for(var i=si2;i<ei2;i+=step){{
        var x=offset+i*cw;
        var dt=new Date(data[i].time*1000);
        ctx.fillText(dt.getHours()+':'+String(dt.getMinutes()).padStart(2,'0'),x,H-8);
    }}
}}
c.addEventListener('wheel',function(e){{
    e.preventDefault();
    var old=cw;
    scale*=e.deltaY>0?0.9:1.1;
    scale=Math.max(2,Math.min(20,scale));
    calcBounds();
    var ratio=cw/old;
    offset=e.clientX-(e.clientX-offset)*ratio;
    draw();
}},{{passive:false}});
c.addEventListener('mousedown',function(e){{dragX=e.clientX}});
c.addEventListener('mousemove',function(e){{
    if(dragX!==null){{offset+=e.clientX-dragX;dragX=e.clientX;draw();return}}
    var rect=c.getBoundingClientRect();
    var mx=e.clientX-rect.left;
    var idx=Math.round((mx-offset)/cw);
    if(idx>=0&&idx<data.length){{
        var d=data[idx];
        var dt=new Date(d.time*1000);
        var pct=((d.close-d.open)/d.open*100);
        tip.style.display='block';
        tip.style.left=(e.clientX+15)+'px';
        tip.style.top=(e.clientY-10)+'px';
        tip.innerHTML='<b>'+dt.toLocaleDateString()+' '+dt.getHours()+':'+String(dt.getMinutes()).padStart(2,'0')+'</b><br>'+
        'O: $'+d.open.toFixed(6)+' H: $'+d.high.toFixed(6)+'<br>'+
        'L: $'+d.low.toFixed(6)+' C: $'+d.close.toFixed(6)+'<br>'+
        '<span style="color:'+(pct>=0?'#00ff88':'#ff4466')+'">'+(pct>=0?'+':'')+pct.toFixed(2)+'%</span>';
    }} else {{tip.style.display='none'}}
}});
c.addEventListener('mouseup',function(){{dragX=null}});
c.addEventListener('mouseleave',function(){{dragX=null;tip.style.display='none'}});
draw();
window.addEventListener('resize',draw);
</script></body></html>"""

with open("chart_test2.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Saved chart_test2.html: {len(html)} bytes")
