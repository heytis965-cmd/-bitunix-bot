
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
html+='<div class="trade-row" onclick="openChart(''+t.symbol+'','+t.entry+','+t.exit+',''+t.side+'',''+(t.reason||'').replace(/'/g,"\'")+'',''+(t.open_time||t.time||'')+'',''+(t.close_time||'')+'')">';
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

