import json
import os
import time
import threading
from datetime import datetime, timezone, timedelta
import calendar
from api_client import BitunixAPI

STATE_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")
AI_MODEL_FILE = os.path.join(os.path.dirname(__file__), "ai_model.json")
PNL_FILE = os.path.join(os.path.dirname(__file__), "pnl_history.json")
TRADES_FILE = os.path.join(os.path.dirname(__file__), "trades_log.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.py")

app = None
bot_ref = None


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def create_dashboard(bot_instance):
    global app, bot_ref
    bot_ref = bot_instance

    try:
        from flask import Flask, render_template_string
    except ImportError:
        print("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)

    HTML = """<!DOCTYPE html><html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Bitunix AI Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#06060f;--card:#0c0c1d;--border:#161630;--accent:#6c5ce7;--accent2:#a29bfe;--green:#00b894;--red:#ff6b6b;--yellow:#feca57;--text:#e0e0e0;--text2:#8a8a9a;--text3:#555566}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);overflow-x:hidden}
.top-bar{background:linear-gradient(135deg,#0c0c1d,#161630);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;backdrop-filter:blur(20px)}
.top-bar h1{font-size:22px;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.top-bar .meta{display:flex;gap:20px;font-size:12px;color:var(--text2)}
.top-bar .meta .dot{width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;margin-right:4px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.main{max-width:1800px;margin:0 auto;padding:20px 24px}
.equity-row{display:grid;grid-template-columns:1fr repeat(5,auto);gap:16px;margin-bottom:20px}
.eq-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px 24px;position:relative;overflow:hidden}
.eq-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.eq-card.main-eq::before{background:linear-gradient(90deg,var(--accent),var(--accent2))}
.eq-card.green::before{background:var(--green)}
.eq-card.red::before{background:var(--red)}
.eq-card.yellow::before{background:var(--yellow)}
.eq-card .label{font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.eq-card .value{font-size:28px;font-weight:700}
.eq-card .sub{font-size:12px;color:var(--text2);margin-top:4px}
.eq-card.main-eq .value{font-size:36px}
.progress-wrap{grid-column:1/-1;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px 24px;display:flex;align-items:center;gap:16px}
.progress-bar{flex:1;height:10px;background:var(--border);border-radius:5px;overflow:hidden}
.progress-fill{height:100%;border-radius:5px;transition:width 0.5s ease;background:linear-gradient(90deg,var(--accent),var(--green))}
.progress-text{font-size:13px;font-weight:600;min-width:50px;text-align:right}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;overflow:hidden}
.card h3{font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;font-size:13px}
.stat-label{color:var(--text2)}
.stat-value{font-weight:600}
.positive{color:var(--green)}.negative{color:var(--red)}.neutral{color:var(--yellow)}
.badge{padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600;display:inline-block}
.badge-long{background:rgba(0,184,148,.15);color:var(--green);border:1px solid rgba(0,184,148,.3)}
.badge-short{background:rgba(255,107,107,.15);color:var(--red);border:1px solid rgba(255,107,107,.3)}
.badge-hold{background:rgba(254,202,87,.15);color:var(--yellow);border:1px solid rgba(254,202,87,.3)}
.badge-tp{background:rgba(0,184,148,.2);color:var(--green);border:1px solid rgba(0,184,148,.4)}
.badge-sl{background:rgba(255,107,107,.2);color:var(--red);border:1px solid rgba(255,107,107,.4)}
.badge-bu{background:rgba(108,92,231,.2);color:var(--accent2);border:1px solid rgba(108,92,231,.4)}
.badge-trail{background:rgba(254,202,87,.2);color:var(--yellow);border:1px solid rgba(254,202,87,.4)}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:10px 8px;color:var(--text2);font-weight:500;border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
td{padding:9px 8px;border-bottom:1px solid rgba(22,22,48,.5)}
tr:hover{background:rgba(108,92,231,.5)}
.calendar{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-top:10px}
.cal-header{text-align:center;font-size:11px;color:var(--text3);padding:6px;font-weight:600}
.cal-day{text-align:center;padding:8px 2px;border-radius:8px;font-size:11px;min-height:52px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:2px;transition:all .2s}
.cal-day:hover{transform:scale(1.05)}
.cal-day.empty{background:transparent}.cal-day.no-data{background:rgba(22,22,48,.5);color:var(--text3)}
.cal-day.positive{background:rgba(0,184,148,.08);border:1px solid rgba(0,184,148,.25)}
.cal-day.negative{background:rgba(255,107,107,.08);border:1px solid rgba(255,107,107,.25)}
.cal-day.today{border:2px solid var(--accent);box-shadow:0 0 12px rgba(108,92,231,.3)}
.cal-day .day-num{font-weight:600;font-size:12px}
.cal-day .day-pnl{font-size:11px;font-weight:600}
.cal-day .day-pct{font-size:10px;color:var(--text2)}
.cal-nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.cal-nav button{background:var(--border);border:1px solid var(--text3);color:var(--text);padding:6px 16px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:500;transition:all .2s}
.cal-nav button:hover{background:var(--accent);border-color:var(--accent)}
.cal-title{font-size:14px;font-weight:600}
.summary-row{display:flex;gap:20px;margin-top:12px;font-size:12px}
.summary-item{display:flex;align-items:center;gap:6px}
.summary-dot{width:10px;height:10px;border-radius:50%}
.dot-green{background:var(--green)}.dot-red{background:var(--red)}.dot-gray{background:var(--text3)}
.sig-row{padding:8px 0;border-bottom:1px solid rgba(22,22,48,.5);display:flex;gap:10px;align-items:center;font-size:12px}
.sig-row:last-child{border-bottom:none}
.date-header{background:var(--accent);color:#fff;font-weight:700;padding:5px 10px;border-radius:4px;margin:8px 0 2px 0;font-size:11px;display:flex;justify-content:space-between;align-items:center}
.date-header:first-child{margin-top:0}
.trade-row{padding:6px 8px;border-bottom:1px solid rgba(22,22,48,.3);display:grid;grid-template-columns:40px 24px 88px 145px 48px 50px 50px 65px;align-items:center;gap:6px;font-size:11px;cursor:pointer;transition:background .2s;border-radius:4px;font-variant-numeric:tabular-nums;text-align:left}
.trade-row:hover{background:rgba(108,92,231,.1)}
.trade-row .time{color:var(--text2);font-variant-numeric:tabular-nums}.trade-row .symbol{font-weight:600}.trade-row .pnl{font-weight:700;font-variant-numeric:tabular-nums}
.empty-state{color:var(--text3);text-align:center;padding:24px;font-size:12px}
#history-container::-webkit-scrollbar{width:6px}
#history-container::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
#history-container::-webkit-scrollbar-track{background:transparent}
.ai-bar{height:6px;background:var(--border);border-radius:3px;overflow:hidden;margin-top:4px}
.ai-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--green))}
.chart-container{position:relative;width:100%;background:#08081a;border-radius:12px;overflow:hidden;margin-top:8px}
.chart-container canvas{width:100%;display:block}
.tooltip{position:fixed;background:rgba(12,12,29,.95);border:1px solid var(--border);padding:10px 14px;border-radius:8px;font-size:12px;pointer-events:none;display:none;z-index:100;white-space:nowrap;backdrop-filter:blur(10px)}
</style></head><body>
<div class="top-bar">
<h1>Bitunix AI Bot</h1>
<div class="meta">
<span><span class="dot"></span> Live</span>
<span id="clock">{{ time }}</span>
</div>
</div>

<div class="main">
<div class="equity-row">
<div class="eq-card main-eq">
<div class="label">Equity</div>
<div class="value {{ 'positive' if session_pnl >= 0 else 'negative' }}" id="equity">${{ "%.2f"|format(equity) }}</div>
<div class="sub">{{ "%+.1f"|format(session_pnl_pct) }}% from ${{ "%.0f"|format(start_balance) }}</div>
</div>
<div class="eq-card green">
<div class="label">Free Balance</div>
<div class="value" id="balance">${{ "%.2f"|format(balance) }}</div>
<div class="sub">Available</div>
</div>
<div class="eq-card">
<div class="label">In Position</div>
<div class="value" id="in-pos">${{ "%.2f"|format(in_positions) }}</div>
<div class="sub">Margin used</div>
</div>
<div class="eq-card {{ 'green' if unrealized >= 0 else 'red' }}">
<div class="label">Unrealized</div>
<div class="value" id="unrealized">{{ "%+.2f"|format(unrealized) }}$</div>
<div class="sub">Open PnL</div>
</div>
<div class="eq-card {{ 'green' if today_pnl >= 0 else 'red' }}">
<div class="label">Today</div>
<div class="value" id="today-pnl">{{ "%+.2f"|format(today_pnl) }}$</div>
<div class="sub" id="today-pct">{{ "%+.1f"|format(today_pnl_pct) }}%</div>
</div>
<div class="eq-card yellow">
<div class="label">Target</div>
<div class="value">${{ "%.0f"|format(target) }}</div>
<div class="sub">Goal</div>
</div>
<div class="progress-wrap">
<span style="font-size:12px;color:var(--text2)">Progress</span>
<div class="progress-bar"><div class="progress-fill" id="bar-fill" style="width:{{ progress }}%"></div></div>
<div class="progress-text" id="progress-text">{{ "%.0f"|format(progress) }}%</div>
</div>
</div>

<div class="grid-3">
<div class="card">
<h3>Performance</h3>
<div class="stat-row"><span class="stat-label">Win Rate</span><span class="stat-value {{ 'positive' if win_rate >= 60 else 'negative' if win_rate < 40 else 'neutral' }}" id="wr-val">{{ "%.1f"|format(win_rate) }}%</span></div>
<div class="stat-row"><span class="stat-label">Wins / Losses</span><span class="stat-value" id="wl-val">{{ wins }}W / {{ losses }}L</span></div>
<div class="stat-row"><span class="stat-label">Total Trades</span><span class="stat-value" id="trades-val">{{ total_trades }}</span></div>
<div class="stat-row"><span class="stat-label">Avg Win</span><span class="stat-value positive">+{{ "%.2f"|format(stats.avg_win) }}%</span></div>
<div class="stat-row"><span class="stat-label">Avg Loss</span><span class="stat-value negative">{{ "%.2f"|format(stats.avg_loss) }}%</span></div>
<div class="stat-row"><span class="stat-label">Total Fees</span><span class="stat-value">${{ "%.2f"|format(total_fees) }}</span></div>
</div>

<div class="card">
<h3>AI Model</h3>
<div class="stat-row"><span class="stat-label">Confidence</span><span class="stat-value">{{ "%.0f"|format(ai.min_confidence * 100) }}%</span></div>
<div class="stat-row"><span class="stat-label">Trades</span><span class="stat-value">{{ ai.total_trades }}</span></div>
<div class="stat-row"><span class="stat-label">Correct</span><span class="stat-value">{{ ai.correct }}</span></div>
<div class="stat-row"><span class="stat-label">Accuracy</span><span class="stat-value">{{ "%.0f"|format((ai.correct / ai.total_trades * 100) if ai.total_trades > 0 else 0) }}%</span></div>
{% for k, v in ai.weights.items() %}
<div class="stat-row"><span class="stat-label" style="font-size:11px">{{ k }}</span><span class="stat-value" style="font-size:11px">{{ "%.2f"|format(v) }}</span></div>
<div class="ai-bar"><div class="ai-fill" style="width:{{ ((v+2)/4*100)|int }}%"></div></div>
{% endfor %}
</div>

<div class="card">
<h3>Market</h3>
<div class="stat-row"><span class="stat-label">BTC</span><span class="stat-value" id="mkt-btc">{{ btc_price }}</span></div>
<div class="stat-row"><span class="stat-label">Signals</span><span class="stat-value" id="mkt-sig">{{ signal_summary }}</span></div>
<div class="stat-row"><span class="stat-label">Trend</span><span class="stat-value {{ 'positive' if market_trend == 'BULL' else 'negative' if market_trend == 'BEAR' else 'neutral' }}" id="mkt-trend">{{ market_trend }}</span></div>
<div class="stat-row"><span class="stat-label">Uptime</span><span class="stat-value">{{ uptime_str }}</span></div>
<div class="stat-row"><span class="stat-label">Trades/hr</span><span class="stat-value">{{ trades_per_hour }}</span></div>
<div class="stat-row"><span class="stat-label">Cycle</span><span class="stat-value">#{{ cycle_count }}</span></div>
<div class="stat-row"><span class="stat-label">Leverage</span><span class="stat-value">{{ leverage }}x</span></div>
</div>
</div>

<div class="card" style="margin-bottom:20px">
<h3>PnL Calendar - {{ cal_title }}</h3>
<div class="cal-nav">
<button onclick="navMonth('{{ prev_month }}')">&larr; Prev</button>
<span class="cal-title">{{ cal_title }}</span>
<button onclick="navMonth('{{ next_month }}')">Next &rarr;</button>
</div>
<div class="calendar">
<div class="cal-header">Mon</div><div class="cal-header">Tue</div><div class="cal-header">Wed</div><div class="cal-header">Thu</div><div class="cal-header">Fri</div><div class="cal-header">Sat</div><div class="cal-header">Sun</div>
{% for day in cal_days %}<div class="cal-day {{ day.cls }} {{ 'today' if day.is_today else '' }}" {{ 'id="cal-today"' if day.is_today else '' }}><span class="day-num">{{ day.num }}</span>{% if day.pnl is not none %}<span class="day-pnl {{ 'positive' if day.pnl >= 0 else 'negative' }}">{{ "%+.1f"|format(day.pnl) }}$</span><span class="day-pct">{{ "%+.1f"|format(day.pct) }}%</span>{% endif %}</div>{% endfor %}
</div>
<div class="summary-row">
<div class="summary-item"><div class="summary-dot dot-green"></div><span>Win Days: {{ profit_days }}</span></div>
<div class="summary-item"><div class="summary-dot dot-red"></div><span>Loss Days: {{ loss_days }}</span></div>
<div class="summary-item"><span>Total: <b class="{{ 'positive' if total_pnl >= 0 else 'negative' }}">{{ "%+.1f"|format(total_pnl) }}$</b></span></div>
</div>
</div>

<div class="grid-2">
<div class="card">
<h3>Open Positions ({{ positions|length }})</h3>
<div id="pos-container">
{% if positions %}<table><tr><th>Side</th><th>Symbol</th><th>Entry</th><th>Current</th><th>TP</th><th>SL</th><th>Margin</th><th>PnL</th><th>Fee</th><th>Trail</th></tr>
{% for p in positions %}<tr><td><span class="badge {{ 'badge-long' if p.side=='LONG' else 'badge-short' }}">{{ p.side }}</span></td><td>{{ p.symbol }}</td><td>${{ "%.4f"|format(p.entry) }}</td><td class="{{ 'positive' if p.unrealized>=0 else 'negative' }}">${{ "%.4f"|format(p.current_price) }}</td><td>${{ "%.4f"|format(p.tp) }}</td><td>${{ "%.4f"|format(p.sl) }}</td><td>${{ "%.2f"|format(p.margin) }}</td><td class="{{ 'positive' if p.unrealized>=0 else 'negative' }}">{{ "%+.2f"|format(p.unrealized) }}</td><td style="color:var(--text2)">${{ "%.3f"|format(p.open_fee) }}</td><td>{{ "ON" if p.trail_active else "" }}</td></tr>{% endfor %}
</table>{% else %}<div class="empty-state">No open positions</div>{% endif %}
</div></div>

<div class="card">
<h3>Top Signals</h3>
<div id="sig-container">
{% for sig in signals %}<div class="sig-row"><span class="badge {{ 'badge-long' if sig.signal=='LONG' else 'badge-short' if sig.signal=='SHORT' else 'badge-hold' }}">{{ sig.signal }}</span><span style="font-weight:500">{{ sig.symbol }}</span><span>${{ "%.4f"|format(sig.price) }}</span><span>S:{{ sig.score }}</span><span>C:{{ sig.confirmations }}</span><span style="color:var(--text2)">4H:{{ sig.mtf_4h }} 1H:{{ sig.mtf_1h }} 5M:{{ sig.mtf_5m }}</span></div>{% else %}<div class="empty-state">No signals</div>{% endfor %}
</div></div>
</div>

<div style="margin-bottom:20px;padding:0">
<h3 style="font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border)">Trade History ({{ closed_trades|length }})</h3>
<div style="max-height:none;overflow-y:auto" id="history-container">
{% set ns = namespace(prev_date='') %}{% for t in closed_trades|reverse %}{% if t.date != ns.prev_date %}{% set ns.prev_date = t.date %}<div class="date-header"><span>{{ t.date }}</span><span style="font-weight:400;font-size:10px;opacity:.8">{{ t.date_summary }}</span></div>{% endif %}<div class="trade-row" data-chart="/chart?symbol={{ t.symbol|urlencode }}&entry={{ t.entry }}&exit={{ t.exit }}&side={{ t.side|urlencode }}&reason={{ t.reason|urlencode }}&open_time={{ t.open_time|urlencode }}&close_time={{ t.close_time|urlencode }}">
<span class="time">{{ t.open_time or t.time }}</span>
<span><span class="badge {{ 'badge-long' if t.side=='LONG' else 'badge-short' }}">{{ t.side[:1] }}</span></span>
<span class="symbol">{{ t.symbol[:10] }}</span>
<span>${{ "%.4f"|format(t.entry) }} {% if t.exit > 0 %}&rarr; ${{ "%.4f"|format(t.exit) }}{% endif %}</span>
<span style="color:var(--text2)">${{ "%.2f"|format(t.margin) }}</span>
<span class="pnl {{ 'positive' if t.pnl>0 else 'negative' if t.pnl<0 else 'neutral' }}">{{ "%+.2f"|format(t.pnl) }}$</span>
<span style="font-size:10px;color:var(--text2)">{{ "%.3f"|format(t.total_fees) }}$</span>
<span><span class="badge badge-{{ 'tp' if t.reason=='TP' else 'sl' if t.reason in ['SL','STOPPED'] else 'trail' if 'Trail' in t.reason else 'bu' }}">{{ t.close_type or t.reason[:10] }}</span></span>
</div>{% endfor %}
{% if not closed_trades %}<div class="empty-state">No completed trades yet</div>{% endif %}
</div>
{% if closed_trades %}<div style="display:flex;gap:20px;padding:12px;border-top:1px solid var(--border);font-size:11px;color:var(--text2)">
<span>Total PnL: <b class="{{ 'positive' if total_closed_pnl > 0 else 'negative' }}">{{ "%+.2f"|format(total_closed_pnl) }}$</b></span>
<span>Total Fees: <b>${{ "%.3f"|format(total_closed_fees) }}</b></span>
<span>Trades: <b>{{ closed_trades|length }}</b></span>
</div>{% endif %}
</div>
</div>

<script>
var updating=false;
function fmt(v,d){return v.toFixed(d===undefined?2:d)}
function cls(v){return v>=0?'positive':'negative'}
function navMonth(m){window.location.href='/?month='+m}
function openChart(sym,entry,exit,side,reason,ot,ct){window.location.href='/chart?symbol='+encodeURIComponent(sym)+'&entry='+encodeURIComponent(entry)+'&exit='+encodeURIComponent(exit)+'&side='+encodeURIComponent(side)+'&reason='+encodeURIComponent(reason)+'&open_time='+encodeURIComponent(ot)+'&close_time='+encodeURIComponent(ct)}
function updateCard(d){
document.getElementById('equity').textContent='$'+fmt(d.equity);
document.getElementById('equity').className='value '+cls(d.session_pnl);
document.getElementById('balance').textContent='$'+fmt(d.balance);
document.getElementById('in-pos').textContent='$'+fmt(d.in_positions);
document.getElementById('unrealized').textContent=fmt(d.unrealized)+'$';
document.getElementById('unrealized').className='value '+cls(d.unrealized);
document.getElementById('today-pnl').textContent=fmt(d.today_pnl)+'$';
document.getElementById('bar-fill').style.width=d.progress+'%';
document.getElementById('progress-text').textContent=fmt(d.progress,0)+'%';
document.getElementById('wr-val').textContent=fmt(d.win_rate,1)+'%';
document.getElementById('wl-val').textContent=d.wins+'W / '+d.losses+'L';
document.getElementById('trades-val').textContent=d.total_trades;
document.getElementById('mkt-btc').textContent=d.btc_price;
document.getElementById('mkt-sig').textContent=d.signal_summary;
document.getElementById('mkt-trend').textContent=d.market_trend;
var posHtml='';
if(d.positions.length===0){posHtml='<div class="empty-state">No positions</div>'}
else{posHtml='<table><tr><th>Side</th><th>Symbol</th><th>Entry</th><th>Current</th><th>TP</th><th>SL</th><th>Margin</th><th>PnL</th><th>Fee</th><th>Trail</th></tr>';
d.positions.forEach(function(p){posHtml+='<tr><td><span class="badge '+(p.side=='LONG'?'badge-long':'badge-short')+'">'+p.side+'</span></td><td>'+p.symbol+'</td><td>$'+fmt(p.entry,4)+'</td><td class="'+cls(p.unrealized)+'">$'+fmt(p.current_price,4)+'</td><td>$'+fmt(p.tp,4)+'</td><td>$'+fmt(p.sl,4)+'</td><td>$'+fmt(p.margin,2)+'</td><td class="'+cls(p.unrealized)+'">'+fmt(p.unrealized)+'</td><td style="color:var(--text2)">$'+fmt(p.open_fee,3)+'</td><td>'+(p.trail_active?'ON':'')+'</td></tr>'});
posHtml+='</table>'}
document.getElementById('pos-container').innerHTML=posHtml;
var sigHtml='';d.signals.forEach(function(s){var b=s.signal==='LONG'?'badge-long':s.signal==='SHORT'?'badge-short':'badge-hold';sigHtml+='<div class="sig-row"><span class="badge '+b+'">'+s.signal+'</span><span style="font-weight:500">'+s.symbol+'</span><span>$'+fmt(s.price,4)+'</span><span>S:'+s.score+'</span><span>C:'+s.confirmations+'</span></div>'});
if(!sigHtml)sigHtml='<div class="empty-state">No signals</div>';
document.getElementById('sig-container').innerHTML=sigHtml;
var hc=document.getElementById('history-container');
if(d.closed_trades&&hc){
var html='';var prevDate='';
var trades=d.closed_trades.slice().reverse();
for(var i=0;i<trades.length;i++){
var t=trades[i];
if(t.date!==prevDate){prevDate=t.date;html+='<div class="date-header"><span>'+t.date+'</span><span style="font-weight:400;font-size:10px;opacity:.8">'+(t.date_summary||'')+'</span></div>'}
var pnlCls=t.pnl>0?'positive':t.pnl<0?'negative':'neutral';
var closeType=t.close_type||((t.reason||'').substring(0,10));
var badgeCls='badge-tp';
if(closeType==='SL'||closeType==='STOPPED')badgeCls='badge-sl';
else if((t.reason||'').indexOf('Trail')>=0)badgeCls='badge-trail';
else if(closeType!=='TP')badgeCls='badge-bu';
var url='/chart?symbol='+encodeURIComponent(t.symbol)+'&entry='+t.entry+'&exit='+t.exit+'&side='+encodeURIComponent(t.side)+'&reason='+encodeURIComponent(t.reason||'')+'&open_time='+encodeURIComponent(t.open_time||t.time||'')+'&close_time='+encodeURIComponent(t.close_time||'');
html+='<div class="trade-row" data-chart="'+url+'">';
html+='<span class="time">'+(t.open_time||t.time||'')+'</span>';
html+='<span><span class="badge '+(t.side=='LONG'?'badge-long':'badge-short')+'">'+t.side.charAt(0)+'</span></span>';
html+='<span class="symbol">'+t.symbol.substring(0,10)+'</span>';
html+='<span>$'+fmt(t.entry,4);
if(t.exit>0)html+=' &rarr; $'+fmt(t.exit,4);
html+='</span>';
html+='<span style="color:var(--text2)">$'+fmt(t.margin,2)+'</span>';
html+='<span class="pnl '+pnlCls+'">'+(t.pnl>=0?'+':'')+fmt(t.pnl)+'$</span>';
html+='<span style="font-size:10px;color:var(--text2)">'+fmt(t.total_fees,3)+'$</span>';
html+='<span><span class="badge '+badgeCls+'">'+closeType+'</span></span>';
html+='</div>'}
if(!html)html='<div class="empty-state">No completed trades yet</div>';
hc.innerHTML=html}
var sumEl=document.querySelector('#history-container+div');
if(sumEl&&d.total_closed_pnl!==undefined){
var tp=d.total_closed_pnl;var tf=d.total_closed_fees;var tc=d.closed_trades?d.closed_trades.length:0;
var cls2=tp>0?'positive':'negative';
sumEl.innerHTML='<span>Total PnL: <b class="'+cls2+'">'+(tp>=0?'+':'')+fmt(tp)+'$</b></span><span>Total Fees: <b>$'+fmt(tf,3)+'</b></span><span>Trades: <b>'+tc+'</b></span>'}
var calToday=document.getElementById('cal-today');
if(calToday&&d.today_pnl!==undefined){
var calCls=d.today_pnl>=0?'positive':'negative';
calToday.className='cal-day '+calCls+' today';
var pnlSpan=calToday.querySelector('.day-pnl');
var pctSpan=calToday.querySelector('.day-pct');
if(pnlSpan){pnlSpan.className='day-pnl '+calCls;pnlSpan.textContent=(d.today_pnl>=0?'+':'')+d.today_pnl.toFixed(1)+'$'}
if(pctSpan)pctSpan.textContent=(d.today_pnl_pct>=0?'+':'')+d.today_pnl_pct.toFixed(1)+'%'}
document.getElementById('today-pnl').textContent=fmt(d.today_pnl)+'$';
document.getElementById('today-pnl').className='value '+cls(d.today_pnl);
document.getElementById('today-pct').textContent=(d.today_pnl_pct>=0?'+':'')+d.today_pnl_pct.toFixed(1)+'%';
document.getElementById('today-pct').className='sub '+cls(d.today_pnl);
}
var histHash='';function poll(){if(updating)return;updating=true;fetch('/api/state').then(function(r){return r.json()}).then(function(d){updateCard(d);updating=false}).catch(function(){updating=false})}
setInterval(poll,3000);
document.addEventListener('click',function(e){var row=e.target.closest('.trade-row[data-chart]');if(row)window.location.href=row.dataset.chart});
</script></body></html>"""

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    @app.route("/static/<path:filename>")
    def serve_static(filename):
        from flask import send_from_directory
        return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), filename)

    @app.route("/chart")
    def chart():
        from flask import request as req
        symbol = req.args.get("symbol", "BTCUSDT")
        try:
            entry = float(req.args.get("entry", 0))
        except (ValueError, TypeError):
            entry = 0.0
        try:
            exit_p = float(req.args.get("exit", 0))
        except (ValueError, TypeError):
            exit_p = 0.0
        side = req.args.get("side", "SHORT")
        reason = req.args.get("reason", "")
        trade_time = req.args.get("time", "")
        open_time = req.args.get("open_time", trade_time)
        close_time = req.args.get("close_time", trade_time)

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", CONFIG_FILE)
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)
            api = BitunixAPI(cfg.API_KEY or "", cfg.API_SECRET or "", "https://fapi.bitunix.com")
            klines_5m = api._get("/api/v1/futures/market/kline", {"symbol": symbol, "interval": "1m", "limit": "500"}, timeout=15)
            data_5m = klines_5m.get("data", []) if klines_5m.get("code") == 0 else []
        except Exception:
            data_5m = []

        candles_5m = "[]"
        if data_5m:
            data_5m = list(reversed(data_5m))
            candles_5m = json.dumps([{"time": int(k["time"]) // 1000, "open": float(k["open"]), "high": float(k["high"]), "low": float(k["low"]), "close": float(k["close"])} for k in data_5m])

        badge_class = "badge-long" if side == "LONG" else "badge-short"
        profit = (exit_p - entry) / entry * 100 if side == "LONG" and entry > 0 else (entry - exit_p) / entry * 100 if entry > 0 else 0
        profit_color = "#00b894" if profit >= 0 else "#ff6b6b"

        CHART_HTML = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{symbol} - {reason}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#06060f;color:#e0e0e0;font-family:'Inter',sans-serif;overflow:hidden}}
        .header{{padding:14px 24px;background:#0c0c1d;border-bottom:1px solid #161630;display:flex;gap:24px;align-items:center;flex-wrap:wrap}}
        .header .symbol{{font-size:20px;font-weight:700;color:#fff}}.badge{{padding:4px 12px;border-radius:8px;font-size:12px;font-weight:600}}
        .badge-long{{background:rgba(0,184,148,.15);color:#00b894;border:1px solid rgba(0,184,148,.3)}}.badge-short{{background:rgba(255,107,107,.15);color:#ff6b6b;border:1px solid rgba(255,107,107,.3)}}
        .info{{display:flex;gap:12px;align-items:center;font-size:13px}}.info .lbl{{color:#8a8a9a}}.info .val{{font-weight:600}}
        .pnl-big{{font-size:22px;font-weight:700}}.help{{position:fixed;bottom:10px;left:50%;transform:translateX(-50%);color:#555566;font-size:11px}}
        canvas{{display:block;cursor:crosshair}}.tooltip{{position:fixed;background:rgba(12,12,29,.95);border:1px solid #161630;padding:10px 14px;border-radius:8px;font-size:12px;pointer-events:none;display:none;z-index:100;white-space:nowrap}}</style></head><body>
        <div class="header"><a href="/" style="color:#6c5ce7;text-decoration:none;font-size:13px">&larr; Back</a><span class="symbol">{symbol}</span><span class="badge {badge_class}">{side}</span>
        <div class="info"><span class="lbl">Entry:</span><span class="val" style="color:#6c5ce7">${entry:.6f}</span></div>
        <div class="info"><span class="lbl">Exit:</span><span class="val" style="color:#00b894">${exit_p:.6f}</span></div>
        <div class="info"><span class="lbl">Reason:</span><span class="val">{reason}</span></div>
        <div class="info"><span class="lbl">Time:</span><span class="val">{trade_time}</span></div>
        <div class="info" style="margin-left:auto"><span class="pnl-big" style="color:{profit_color}">{"+"if profit>=0 else ""}{profit:.2f}%</span></div></div>
        <div class="tooltip" id="tip"></div><canvas id="c"></canvas>
        <div class="help">Scroll: zoom | Drag: pan | Hover: candle info</div>
        <script>var data={candles_5m};var entryP={entry};var exitP={exit_p};var side='{side}';var profitPct={profit};
        var ot='{open_time}';var ct='{close_time}';
        var c=document.getElementById('c');var ctx=c.getContext('2d');var tip=document.getElementById('tip');
        var offset=0;var scale=4;var dragX=null;var W,H,cw,ph,mn,mx;var drawn=false;
        var entryIdx=-1,exitIdx=-1;
        var otParts=ot.split(':');var otH=parseInt(otParts[0]||'0')-5;var otM=parseInt(otParts[1]||'0');
        if(otH<0)otH+=24;
        var ctParts=ct.split(':');var ctH=parseInt(ctParts[0]||'0')-5;var ctM=parseInt(ctParts[1]||'0');
        if(ctH<0)ctH+=24;
        var otTotalMin=otH*60+otM;var ctTotalMin=ctH*60+ctM;
        var priceE=[],timeE=[];
        for(var i=0;i<data.length;i++){{var d=data[i];var dt=new Date(d.time*1000);
        var dMin=dt.getUTCHours()*60+dt.getUTCMinutes();
        var inRange=(entryP>=d.low&&entryP<=d.high);
        var dtE=Math.abs(dMin-otTotalMin);
        if(inRange)priceE.push({{i:i,dist:dtE}});timeE.push({{i:i,dist:dtE}})}}
        priceE.sort(function(a,b){{return a.dist-b.dist}});
        timeE.sort(function(a,b){{return a.dist-b.dist}});
        if(priceE.length>0)entryIdx=priceE[0].i;else if(timeE.length>0)entryIdx=timeE[0].i;
        var priceX=[],timeX=[];
        for(var i=0;i<data.length;i++){{var d=data[i];var dt=new Date(d.time*1000);
        var dMin=dt.getUTCHours()*60+dt.getUTCMinutes();
        var inRange=(exitP>=d.low&&exitP<=d.high);
        var dtX=Math.abs(dMin-ctTotalMin);
        if(inRange)priceX.push({{i:i,dist:dtX}});timeX.push({{i:i,dist:dtX}})}}
        priceX.sort(function(a,b){{return a.dist-b.dist}});
        timeX.sort(function(a,b){{return a.dist-b.dist}});
        if(priceX.length>0)exitIdx=priceX[0].i;else if(timeX.length>0)exitIdx=timeX[0].i;
        if(entryIdx<0){{entryIdx=Math.max(0,Math.floor(data.length*0.4))}}
        if(exitIdx<0){{exitIdx=Math.max(0,Math.floor(data.length*0.6))}}
        function calcBounds(){{var si=Math.max(0,Math.floor(-offset/cw));var ei=Math.min(data.length,Math.ceil((W-offset)/cw));var all=[];for(var i=si;i<ei;i++){{all.push(data[i].low,data[i].high)}}all.push(entryP,exitP);mn=Math.min.apply(null,all);mx=Math.max.apply(null,all);var pad=(mx-mn)*0.25;mn-=pad;mx+=pad;ph=H/(mx-mn)}}
        function priceY(p){{return H-(p-mn)*ph}}
        function draw(){{c.width=window.innerWidth;c.height=window.innerHeight-50;W=c.width;H=c.height;
        if(!drawn&&entryIdx>=0){{var cw3=Math.max(2,scale);var minIdx=Math.min(entryIdx,exitIdx);var maxIdx=Math.max(entryIdx,exitIdx);var centerIdx=(minIdx+maxIdx)/2;var rangePx=(maxIdx-minIdx)*cw3;var viewW=W*0.8;if(rangePx>viewW){{cw3=viewW/(maxIdx-minIdx);scale=cw3;cw=cw3}}offset=W/2-centerIdx*cw3;drawn=true}}
        ctx.fillStyle='#06060f';ctx.fillRect(0,0,W,H);if(!data.length)return;cw=Math.max(2,scale);calcBounds();ctx.fillStyle='#0c0c1d';ctx.fillRect(0,H-24,W,24);
        var si=Math.max(0,Math.floor(-offset/cw));var ei=Math.min(data.length,Math.ceil((W-offset)/cw));
        for(var i=si;i<ei;i++){{var d=data[i];var x=offset+i*cw;if(x<-cw*2||x>W+cw*2)continue;
        var oY=priceY(d.open);var cY=priceY(d.close);var hY=priceY(d.high);var lY=priceY(d.low);
        var bull=d.close>=d.open;var bodyTop=Math.min(oY,cY);var bodyH=Math.max(1,Math.abs(cY-oY));
        ctx.strokeStyle=bull?'#00b894':'#ff6b6b';ctx.lineWidth=Math.max(1,cw*0.1);ctx.beginPath();ctx.moveTo(x,hY);ctx.lineTo(x,lY);ctx.stroke();
        ctx.fillStyle=bull?'#00b894':'#ff6b6b';ctx.fillRect(x-cw*0.35,bodyTop,cw*0.7,bodyH)}}
        var eCandle=entryIdx>=0?data[entryIdx]:null;var xCandle=exitIdx>=0?data[exitIdx]:null;
        var eY=priceY(eCandle?eCandle.close:entryP);var xY=priceY(xCandle?xCandle.close:exitP);var eX=offset+entryIdx*cw;var xX=offset+exitIdx*cw;
        ctx.fillStyle=profitPct>=0?'rgba(0,184,148,0.06)':'rgba(255,107,107,0.06)';ctx.fillRect(0,Math.min(eY,xY),W,Math.abs(xY-eY)||2);
        ctx.setLineDash([6,4]);ctx.lineWidth=1;ctx.strokeStyle='rgba(108,92,231,0.4)';ctx.beginPath();ctx.moveTo(0,eY);ctx.lineTo(W,eY);ctx.stroke();
        ctx.strokeStyle='rgba(0,184,148,0.4)';ctx.beginPath();ctx.moveTo(0,xY);ctx.lineTo(W,xY);ctx.stroke();ctx.setLineDash([]);
        ctx.beginPath();ctx.moveTo(eX,eY);ctx.lineTo(xX,xY);ctx.strokeStyle=profitPct>=0?'#00b894':'#ff6b6b';ctx.lineWidth=2;ctx.stroke();
        function dot(px,py,color,label,price,above){{ctx.beginPath();ctx.arc(px,py,5,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();ctx.font='bold 10px sans-serif';ctx.textAlign='center';ctx.fillStyle=color;var ly=above?py-14:py+20;ctx.fillText(label,px,ly);ctx.fillStyle='#8a8a9a';ctx.font='9px sans-serif';ctx.fillText('$'+price.toFixed(6),px,above?ly-12:ly+12)}}
        if(entryIdx>=0){{dot(eX,eY,'#6c5ce7','ENTRY',entryP,side=='LONG')}}
        if(exitIdx>=0){{dot(xX,xY,'#00b894','EXIT',exitP,side!='LONG')}}
        if(entryIdx>=0&&exitIdx>=0){{var midX2=(eX+xX)/2;var midY2=Math.min(eY,xY)-24;if(midY2<20)midY2=Math.max(eY,xY)+30;
        var txt=(profitPct>=0?'+':'')+profitPct.toFixed(2)+'%';ctx.font='bold 13px sans-serif';ctx.textAlign='center';
        var tw2=ctx.measureText(txt).width+12;ctx.fillStyle='#0c0c1d';ctx.fillRect(midX2-tw2/2,midY2-11,tw2,18);
        ctx.strokeStyle=profitPct>=0?'#00b894':'#ff6b6b';ctx.lineWidth=1;ctx.strokeRect(midX2-tw2/2,midY2-11,tw2,18);
        ctx.fillStyle=profitPct>=0?'#00b894':'#ff6b6b';ctx.fillText(txt,midX2,midY2+2);ctx.textAlign='left'}}
        var step=Math.max(1,Math.floor((ei-si)/12));ctx.fillStyle='#555566';ctx.font='10px sans-serif';ctx.textAlign='center';
        for(var i=si;i<ei;i+=step){{var x=offset+i*cw+cw/2;if(x<0||x>W)continue;var dt=new Date(data[i].time*1000);var hh=String(dt.getHours()).padStart(2,'0');var mm=String(dt.getMinutes()).padStart(2,'0');var dd=dt.getDate()+'/'+(dt.getMonth()+1);if(step>30)ctx.fillText(dd,x,H-8);else ctx.fillText(hh+':'+mm,x,H-8)}}ctx.textAlign='left'}}
        c.addEventListener('wheel',function(e){{e.preventDefault();var mx2=e.clientX;var oldCW=cw;scale*=e.deltaY>0?0.85:1.15;scale=Math.max(1.5,Math.min(30,scale));cw=Math.max(2,scale);offset=mx2-(mx2-offset)*(cw/oldCW);draw()}},{{passive:false}});
        c.addEventListener('mousedown',function(e){{dragX=e.clientX}});
        c.addEventListener('mousemove',function(e){{if(dragX!==null){{offset+=e.clientX-dragX;dragX=e.clientX;draw();return}}var rect=c.getBoundingClientRect();var mx3=e.clientX-rect.left;var idx=Math.round((mx3-offset)/cw);if(idx>=0&&idx<data.length){{var d=data[idx];var dt=new Date(d.time*1000);var chg=((d.close-d.open)/d.open*100);var col=chg>=0?'#00b894':'#ff6b6b';tip.style.display='block';tip.style.left=(e.clientX+15)+'px';tip.style.top=(e.clientY-10)+'px';tip.innerHTML='<b style="color:#fff">'+dt.toLocaleDateString()+' '+String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0')+'</b><br><span style="color:#8a8a9a">O:</span> $'+d.open.toFixed(6)+'  <span style="color:#8a8a9a">H:</span> $'+d.high.toFixed(6)+'<br><span style="color:#8a8a9a">L:</span> $'+d.low.toFixed(6)+'  <span style="color:#8a8a9a">C:</span> $'+d.close.toFixed(6)+'<br><span style="color:'+col+'">'+(chg>=0?'+':'')+chg.toFixed(2)+'%</span>'}}else tip.style.display='none'}});
        c.addEventListener('mouseup',function(){{dragX=null}});c.addEventListener('mouseleave',function(){{dragX=null;tip.style.display='none'}});
        draw();window.addEventListener('resize',draw);</script></body></html>"""
        return CHART_HTML

    def _build_data():
        state = read_json(STATE_FILE)
        stats = read_json(STATS_FILE)
        ai = read_json(AI_MODEL_FILE)
        pnl_data = read_json(PNL_FILE)

        balance = state.get("balance", 0)
        positions = state.get("positions", [])
        start_balance = state.get("start_balance", 25)
        in_positions = sum(p.get("margin", 0) for p in positions)
        unrealized = sum(p.get("unrealized", 0) for p in positions)
        equity = balance + in_positions + unrealized
        day_start_eq = state.get("day_start_eq", start_balance)

        today_pnl = equity - day_start_eq
        today_pnl_pct = (today_pnl / day_start_eq * 100) if day_start_eq else 0
        session_pnl = equity - start_balance
        session_pnl_pct = (session_pnl / start_balance * 100) if start_balance else 0

        target = getattr(bot_ref, "target", 500.0) if bot_ref else 500.0
        progress = min(equity / target * 100, 100)
        total_trades = state.get("total_trades", 0)
        wins = state.get("wins", 0)
        losses = state.get("losses", 0)
        win_rate = (wins / total_trades * 100) if total_trades else 0

        for p in positions:
            p["unrealized"] = p.get("unrealized", 0)
            p["trail_active"] = p.get("trail_active", False)
            p["current_price"] = p.get("current_price", p.get("entry", 0))

        signals = getattr(bot_ref, "last_signals", []) if bot_ref else []

        try:
            with open(TRADES_FILE, "r", encoding="utf-8") as f:
                all_trades = json.load(f)
                closed_trades = [t for t in all_trades if t.get("exit", 0) > 0]
                for t in closed_trades:
                    if "total_fees" not in t:
                        t["total_fees"] = t.get("fees", 0)
                    if "close_type" not in t:
                        r = t.get("reason", "")
                        if "TP" in r: t["close_type"] = "TP"
                        elif "SL" in r or "STOPPED" in r: t["close_type"] = "SL"
                        elif "Trail" in r: t["close_type"] = "Trail"
                        elif "STAGNANT" in r: t["close_type"] = "STAGN"
                        elif "FUNDING" in r: t["close_type"] = "FUNDING"
                        else: t["close_type"] = r[:8]
                    if "open_time" not in t:
                        t["open_time"] = t.get("time", "")
                grouped = {}
                for t in closed_trades:
                    d = t.get("date", "")
                    if d not in grouped:
                        grouped[d] = []
                    grouped[d].append(t)
                for d in grouped:
                    day_pnl = sum(t.get("pnl", 0) for t in grouped[d])
                    wins_d = sum(1 for t in grouped[d] if t.get("pnl", 0) > 0)
                    total_d = len(grouped[d])
                    wr_d = f"{wins_d}/{total_d}" if total_d else "0"
                    for t in grouped[d]:
                        t["date_summary"] = f"PnL: {'+'if day_pnl>=0 else ''}{day_pnl:.2f}$ | {wr_d} W/R"
        except Exception:
            closed_trades = []

        total_closed_pnl = sum(t.get("pnl", 0) for t in closed_trades)
        total_closed_fees = sum(t.get("total_fees", 0) for t in closed_trades)

        now = datetime.now(timezone.utc)
        today_str = (now + timedelta(hours=5)).strftime("%Y-%m-%d")

        month_param = None
        try:
            from flask import request as req
            month_param = req.args.get("month")
        except Exception:
            pass

        if month_param:
            try:
                y, m = map(int, month_param.split("-"))
                cal_date = now.replace(year=y, month=m, day=1)
            except Exception:
                cal_date = now.replace(day=1)
        else:
            cal_date = now.replace(day=1)

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(cal_date.year, cal_date.month)

        cal_days = []
        profit_days = 0
        loss_days = 0
        total_pnl_cal = 0.0

        for week in month_days:
            for d in week:
                if d == 0:
                    cal_days.append({"num": "", "cls": "empty", "is_today": False, "pnl": None, "pct": None})
                else:
                    date_str = f"{cal_date.year}-{cal_date.month:02d}-{d:02d}"
                    is_today = (date_str == today_str)
                    if is_today:
                        pnl = today_pnl
                        pct = today_pnl_pct
                        total_pnl_cal += pnl
                        cls_name = "positive" if pnl >= 0 else "negative"
                        cal_days.append({"num": d, "cls": cls_name, "is_today": is_today, "pnl": pnl, "pct": pct})
                    elif date_str in pnl_data:
                        day_data = pnl_data[date_str]
                        pnl = day_data.get("pnl_usd", 0)
                        pct = day_data.get("pnl_pct", 0)
                        total_pnl_cal += pnl
                        cls_name = "positive" if pnl >= 0 else "negative"
                        profit_days += 1 if pnl >= 0 else 0
                        loss_days += 1 if pnl < 0 else 0
                        cal_days.append({"num": d, "cls": cls_name, "is_today": is_today, "pnl": pnl, "pct": pct})
                    else:
                        cal_days.append({"num": d, "cls": "no-data", "is_today": is_today, "pnl": None, "pct": None})

        prev_month = (cal_date.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        next_month = (cal_date.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m")
        cal_title = cal_date.strftime("%B %Y")

        elapsed = 0
        if bot_ref and hasattr(bot_ref, "start_time"):
            st = bot_ref.start_time
            if isinstance(st, (int, float)):
                elapsed = time.time() - st
            else:
                elapsed = (now - st).total_seconds()
        elapsed_min = elapsed / 60
        uptime_str = "<1m" if elapsed_min < 1 else f"{elapsed_min:.0f}m" if elapsed_min < 60 else f"{elapsed_min/60:.1f}h"
        trades_per_hour = f"{total_trades / (elapsed / 3600):.1f}" if elapsed > 60 else "0"

        btc_price = "-"
        try:
            api = BitunixAPI("", "", "https://fapi.bitunix.com")
            resp = api._get("/api/v1/futures/market/kline", {"symbol": "BTCUSDT", "interval": "1m", "limit": "1"}, timeout=5)
            if resp.get("code") == 0 and resp.get("data"):
                btc_price = f"${float(resp['data'][0]['close']):,.0f}"
        except Exception:
            pass

        long_sigs = sum(1 for s in signals if s.get("signal") == "LONG")
        short_sigs = sum(1 for s in signals if s.get("signal") == "SHORT")
        signal_summary = f"{long_sigs}L {short_sigs}S"
        market_trend = "BEAR" if short_sigs > long_sigs else "BULL" if long_sigs > short_sigs else "NEUTRAL"

        return {
            "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "balance": balance, "equity": equity, "start_balance": start_balance,
            "today_pnl": today_pnl, "today_pnl_pct": today_pnl_pct,
            "session_pnl": session_pnl, "session_pnl_pct": session_pnl_pct,
            "target": target, "progress": progress, "total_trades": total_trades,
            "wins": wins, "losses": losses, "win_rate": win_rate,
            "stats": {"avg_win": stats.get("avg_win", 0), "avg_loss": stats.get("avg_loss", 0)},
            "total_fees": state.get("total_fees", 0), "cycle_count": state.get("cycle_count", 0),
            "ai": {"weights": ai.get("weights", {}), "min_confidence": ai.get("min_confidence", 0.50),
                   "total_trades": ai.get("total_trades", 0), "correct": ai.get("correct", 0)},
            "leverage": getattr(bot_ref, "leverage", 5) if bot_ref else 5,
            "positions": positions, "signals": signals,
            "closed_trades": closed_trades,
            "total_closed_pnl": total_closed_pnl, "total_closed_fees": total_closed_fees,
            "in_positions": in_positions, "unrealized": unrealized,
            "cal_days": cal_days, "cal_title": cal_title,
            "prev_month": prev_month, "next_month": next_month,
            "profit_days": profit_days, "loss_days": loss_days,
            "total_pnl": total_pnl_cal,
            "btc_price": btc_price, "signal_summary": signal_summary, "market_trend": market_trend,
            "uptime_str": uptime_str, "trades_per_hour": trades_per_hour,
        }

    @app.route("/api/state")
    def api_state():
        from flask import jsonify
        return jsonify(_build_data())

    @app.route("/")
    def index():
        d = _build_data()
        return render_template_string(HTML, **d)

    return app


def start_dashboard(bot_instance, port=None):
    app = create_dashboard(bot_instance)
    if app is None:
        return
    if port is None:
        port = int(os.environ.get("PORT", 5000))
    thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False), daemon=True)
    thread.start()
    print(f"Dashboard running at http://localhost:{port}")
