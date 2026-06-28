import json
import os
from flask import Flask, render_template_string, request
from api_client import BitunixAPI

app = Flask(__name__)
TRADES_FILE = os.path.join(os.path.dirname(__file__), "trades_log.json")


def load_trades():
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@app.route("/")
def index():
    trades = load_trades()
    rows = ""
    for i, t in enumerate(trades):
        if t.get("exit", 0) == 0:
            continue
        pnl_cls = "pos" if t["pnl"] > 0 else "neg" if t["pnl"] < 0 else ""
        rows += f"""<a class="row {pnl_cls}" href="/chart?idx={i}">
            <span class="time">{t.get('time','')}</span>
            <span class="badge {'bl' if t['side']=='LONG' else 'bs'}">{t['side']}</span>
            <span class="sym">{t['symbol']}</span>
            <span>${t['entry']:.4f} → ${t['exit']:.4f}</span>
            <span class="pnl {'pos' if t['pnl']>0 else 'neg'}">{t['pnl']:+.2f}$</span>
            <span class="reason">{t['reason']}</span>
        </a>"""
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Графики сделок</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{background:#0a0a1a;color:#e0e0e0;font-family:'Segoe UI',sans-serif;padding:20px}}
        h1{{color:#00d4ff;margin-bottom:15px;font-size:20px}}
        .row{{display:flex;gap:12px;align-items:center;padding:8px 12px;border-bottom:1px solid #1a1a2e;text-decoration:none;color:inherit;font-size:13px}}
        .row:hover{{background:#12122a}}
        .badge{{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700}}
        .bl{{background:#00ff8822;color:#00ff88}}.bs{{background:#ff446622;color:#ff4466}}
        .sym{{width:110px;font-weight:600}}
        .time{{width:50px;color:#666}}
        .pnl{{width:70px;font-weight:600}}
        .reason{{color:#888;font-size:11px}}
        .pos{{color:#00ff88}}.neg{{color:#ff4466}}
    </style></head><body>
    <h1>Графики сделок ({len([t for t in trades if t.get('exit',0)!=0])})</h1>
    {rows if rows else '<p style="color:#666">Нет закрытых сделок</p>'}
    </body></html>"""
    return html


@app.route("/chart")
def chart():
    idx = int(request.args.get("idx", 0))
    trades = load_trades()
    if idx < 0 or idx >= len(trades):
        return "Not found", 404
    t = trades[idx]
    symbol = t["symbol"]
    entry = t["entry"]
    exit_p = t["exit"]
    side = t["side"]
    reason = t["reason"]
    trade_time = t.get("time", "")

    try:
        api = BitunixAPI("", "", "https://fapi.bitunix.com")
        klines_5m = api._get("/api/v1/futures/market/kline",
                             {"symbol": symbol, "interval": "5m", "limit": "200"}, timeout=15)
        data_5m = klines_5m.get("data", []) if klines_5m.get("code") == 0 else []
    except Exception:
        data_5m = []

    candles_5m = "[]"
    if data_5m:
        data_5m = list(reversed(data_5m))
        candles_5m = json.dumps([{
            "time": int(k["time"]) // 1000,
            "open": float(k["open"]),
            "high": float(k["high"]),
            "low": float(k["low"]),
            "close": float(k["close"]),
        } for k in data_5m])

    profit = (exit_p - entry) / entry * 100 if side == "LONG" else (entry - exit_p) / entry * 100
    profit_color = "#00c853" if profit >= 0 else "#ef5350"
    profit_sign = "+" if profit >= 0 else ""
    badge_class = "bl" if side == "LONG" else "bs"

    CHART_HTML = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{symbol} - {reason}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0a0a1a; color:#e0e0e0; font-family:'Segoe UI',sans-serif; overflow:hidden; }}
        .header {{ padding:12px 20px; background:#12122a; border-bottom:1px solid #1e1e3a; display:flex; gap:20px; align-items:center; flex-wrap:wrap; }}
        .header .symbol {{ font-size:18px; font-weight:700; color:#fff; }}
        .badge {{ padding:3px 10px; border-radius:4px; font-size:11px; font-weight:700; }}
        .bl {{ background:#00ff8822; color:#00ff88; border:1px solid #00ff8844; }}
        .bs {{ background:#ff446622; color:#ff4466; border:1px solid #ff446644; }}
        .info-group {{ display:flex; gap:8px; align-items:center; font-size:13px; }}
        .info-group .label {{ color:#666; }}
        .info-group .val {{ font-weight:600; }}
        .pnl-big {{ font-size:20px; font-weight:700; }}
        .help {{ position:fixed; bottom:8px; left:50%; transform:translateX(-50%); color:#444; font-size:11px; }}
        canvas {{ display:block; cursor:crosshair; }}
        .tooltip {{ position:fixed; background:#1a1a2e; border:1px solid #333; padding:8px 12px; border-radius:6px; font-size:12px; pointer-events:none; display:none; z-index:100; white-space:nowrap; }}
    </style></head><body>
    <div class="header">
        <span class="symbol">{symbol}</span>
        <span class="badge {badge_class}">{side}</span>
        <div class="info-group">
            <span class="label">Вход:</span>
            <span class="val" style="color:#ffaa00">${{entry:.6f}}</span>
        </div>
        <div class="info-group">
            <span class="label">Выход:</span>
            <span class="val" style="color:#00d4ff">${{exit_p:.6f}}</span>
        </div>
        <div class="info-group">
            <span class="label">Причина:</span>
            <span class="val">{reason}</span>
        </div>
        <div class="info-group">
            <span class="label">Время:</span>
            <span class="val">{trade_time}</span>
        </div>
        <div class="info-group" style="margin-left:auto;">
            <span class="pnl-big" style="color:{profit_color}">{profit_sign}{{profit:.2f}}%</span>
        </div>
    </div>
    <div class="tooltip" id="tip"></div>
    <canvas id="c"></canvas>
    <div class="help">Прокрутка: зум | Перетаскивание: навигация | Наведение: информация о свече</div>
    <script>
    var data = {candles_5m};
    var entryP = {entry};
    var exitP = {exit_p};
    var side = '{side}';
    var profitPct = {profit};
    var c = document.getElementById('c');
    var ctx = c.getContext('2d');
    var tip = document.getElementById('tip');
    var offset = 0;
    var scale = 4;
    var dragX = null;
    var W, H, cw, ph, mn, mx;
    var drawn = false;

    var entryIdx = -1, exitIdx = -1;
    var bestED = Infinity, bestXD = Infinity;
    for(var i=0;i<data.length;i++){{
        var d = data[i];
        var de = Math.abs(((d.high+d.low)/2) - entryP);
        var dx = Math.abs(((d.high+d.low)/2) - exitP);
        if(de < bestED){{bestED = de; entryIdx = i;}}
        if(dx < bestXD){{bestXD = dx; exitIdx = i;}}
    }}

    function calcBounds(){{
        var si = Math.max(0, Math.floor(-offset/cw));
        var ei = Math.min(data.length, Math.ceil((W-offset)/cw));
        var all = [];
        for(var i=si;i<ei;i++){{all.push(data[i].low,data[i].high)}}
        all.push(entryP,exitP);
        mn = Math.min.apply(null,all);
        mx = Math.max.apply(null,all);
        var pad = (mx-mn)*0.25;
        mn -= pad; mx += pad;
        ph = H/(mx-mn);
    }}

    function priceY(p){{return H-(p-mn)*ph;}}

    function draw(){{
        c.width = window.innerWidth;
        c.height = window.innerHeight - 50;
        W = c.width; H = c.height;
        if(!drawn && entryIdx >= 0){{
            var cw3 = Math.max(2, scale);
            offset = W/2 - Math.max(entryIdx, exitIdx) * cw3;
            drawn = true;
        }}
        ctx.fillStyle = '#0a0a1a';
        ctx.fillRect(0,0,W,H);
        if(!data.length) return;

        cw = Math.max(2, scale);
        calcBounds();

        ctx.fillStyle = '#111';
        ctx.fillRect(0,H-24,W,24);

        var si = Math.max(0, Math.floor(-offset/cw));
        var ei = Math.min(data.length, Math.ceil((W-offset)/cw));

        for(var i=si;i<ei;i++){{
            var d = data[i];
            var x = offset + i*cw;
            if(x < -cw*2 || x > W+cw*2) continue;

            var oY = priceY(d.open);
            var cY = priceY(d.close);
            var hY = priceY(d.high);
            var lY = priceY(d.low);

            var bull = d.close >= d.open;
            var bodyTop = Math.min(oY, cY);
            var bodyH = Math.max(1, Math.abs(cY - oY));

            ctx.strokeStyle = bull ? '#00c853' : '#ef5350';
            ctx.lineWidth = Math.max(1, cw*0.1);
            ctx.beginPath();
            ctx.moveTo(x, hY);
            ctx.lineTo(x, lY);
            ctx.stroke();

            ctx.fillStyle = bull ? '#00c853' : '#ef5350';
            ctx.fillRect(x - cw*0.35, bodyTop, cw*0.7, bodyH);
        }}

        var eY = priceY(entryP);
        var xY = priceY(exitP);
        var eX = offset + entryIdx*cw;
        var xX = offset + exitIdx*cw;

        ctx.fillStyle = profitPct >= 0 ? 'rgba(0,200,83,0.06)' : 'rgba(239,83,80,0.06)';
        ctx.fillRect(0, Math.min(eY,xY), W, Math.abs(xY-eY) || 2);

        ctx.setLineDash([6,4]);
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(255,170,0,0.4)';
        ctx.beginPath(); ctx.moveTo(0,eY); ctx.lineTo(W,eY); ctx.stroke();
        ctx.strokeStyle = 'rgba(0,212,255,0.4)';
        ctx.beginPath(); ctx.moveTo(0,xY); ctx.lineTo(W,xY); ctx.stroke();
        ctx.setLineDash([]);

        ctx.beginPath();
        ctx.moveTo(eX, eY);
        ctx.lineTo(xX, xY);
        ctx.strokeStyle = profitPct >= 0 ? '#00c853' : '#ef5350';
        ctx.lineWidth = 2;
        ctx.stroke();

        function dot(px, py, color, label, price, above){{
            ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI*2);
            ctx.fillStyle = color; ctx.fill();
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();

            ctx.font = 'bold 10px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillStyle = color;
            var ly = above ? py - 14 : py + 20;
            ctx.fillText(label, px, ly);
            ctx.fillStyle = '#999';
            ctx.font = '9px sans-serif';
            ctx.fillText('$' + price.toFixed(6), px, above ? ly - 12 : ly + 12);
        }}

        if(entryIdx >= 0){{
            var lbl = side == 'LONG' ? '\\u25B2 \\u0412\\u0425\\u041E\\u0414' : '\\u25BC \\u0412\\u0425\\u041E\\u0414';
            dot(eX, eY, '#ffaa00', lbl, entryP, side == 'LONG');
        }}
        if(exitIdx >= 0){{
            var lbl = side == 'LONG' ? '\\u25BC \\u0412\\u042B\\u0425\\u041E\\u0414' : '\\u25B2 \\u0412\\u042B\\u0425\\u041E\\u0414';
            dot(xX, xY, '#00d4ff', lbl, exitP, side != 'LONG');
        }}

        if(entryIdx >= 0 && exitIdx >= 0){{
            var midX2 = (eX + xX) / 2;
            var midY2 = Math.min(eY, xY) - 24;
            if(midY2 < 20) midY2 = Math.max(eY, xY) + 30;
            var txt = (profitPct>=0?'+':'') + profitPct.toFixed(2) + '%';
            ctx.font = 'bold 13px sans-serif';
            ctx.textAlign = 'center';
            var tw2 = ctx.measureText(txt).width + 12;
            ctx.fillStyle = '#0a0a1a';
            ctx.fillRect(midX2 - tw2/2, midY2 - 11, tw2, 18);
            ctx.strokeStyle = profitPct >= 0 ? '#00c853' : '#ef5350';
            ctx.lineWidth = 1;
            ctx.strokeRect(midX2 - tw2/2, midY2 - 11, tw2, 18);
            ctx.fillStyle = profitPct >= 0 ? '#00c853' : '#ef5350';
            ctx.fillText(txt, midX2, midY2 + 2);
            ctx.textAlign = 'left';
        }}

        var step = Math.max(1, Math.floor((ei-si)/12));
        ctx.fillStyle = '#555';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        for(var i=si;i<ei;i+=step){{
            var x = offset + i*cw + cw/2;
            if(x < 0 || x > W) continue;
            var dt = new Date(data[i].time*1000);
            var hh = String(dt.getHours()).padStart(2,'0');
            var mm = String(dt.getMinutes()).padStart(2,'0');
            ctx.fillText(hh+':'+mm, x, H-8);
        }}
        ctx.textAlign = 'left';
    }}

    c.addEventListener('wheel', function(e){{
        e.preventDefault();
        var mx2 = e.clientX;
        var oldCW = cw;
        scale *= e.deltaY > 0 ? 0.85 : 1.15;
        scale = Math.max(1.5, Math.min(30, scale));
        cw = Math.max(2, scale);
        offset = mx2 - (mx2 - offset) * (cw / oldCW);
        draw();
    }}, {{passive:false}});

    c.addEventListener('mousedown', function(e){{ dragX = e.clientX; }});
    c.addEventListener('mousemove', function(e){{
        if(dragX !== null){{ offset += e.clientX - dragX; dragX = e.clientX; draw(); return; }}
        var rect = c.getBoundingClientRect();
        var mx3 = e.clientX - rect.left;
        var idx = Math.round((mx3 - offset) / cw);
        if(idx >= 0 && idx < data.length){{
            var d = data[idx];
            var dt = new Date(d.time*1000);
            var chg = ((d.close - d.open) / d.open * 100);
            var col = chg >= 0 ? '#00c853' : '#ef5350';
            tip.style.display = 'block';
            tip.style.left = (e.clientX + 15) + 'px';
            tip.style.top = (e.clientY - 10) + 'px';
            tip.innerHTML =
                '<b style="color:#fff">' + dt.toLocaleDateString('ru') + ' ' +
                String(dt.getHours()).padStart(2,'0') + ':' + String(dt.getMinutes()).padStart(2,'0') + '</b><br>' +
                '<span style="color:#888">O:</span> $' + d.open.toFixed(6) +
                '  <span style="color:#888">H:</span> $' + d.high.toFixed(6) + '<br>' +
                '<span style="color:#888">L:</span> $' + d.low.toFixed(6) +
                '  <span style="color:#888">C:</span> $' + d.close.toFixed(6) + '<br>' +
                '<span style="color:' + col + '">' + (chg>=0?'+':'') + chg.toFixed(2) + '%</span>';
        }} else {{ tip.style.display = 'none'; }}
    }});
    c.addEventListener('mouseup', function(){{ dragX = null; }});
    c.addEventListener('mouseleave', function(){{ dragX = null; tip.style.display = 'none'; }});

    draw();
    window.addEventListener('resize', draw);
    </script></body></html>"""
    return CHART_HTML


if __name__ == "__main__":
    print("=" * 50)
    print("  Просмотрщик графиков")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
