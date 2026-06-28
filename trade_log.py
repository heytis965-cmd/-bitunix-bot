import json
import os

TRADES_FILE = os.path.join(os.path.dirname(__file__), "trades_log.json")


def load_trades():
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_trades(data):
    try:
        with open(TRADES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def log_trade(symbol, side, entry, exit_price, margin, pnl, reason, time_str, funding=0, fees=0):
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc) + timedelta(hours=5)
    months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
    date_str = str(now.day) + " " + months[now.month - 1]
    time_now = now.strftime("%H:%M")
    trades = load_trades()
    if reason == "OPEN":
        trades.append({
            "date": date_str,
            "symbol": symbol,
            "side": side,
            "entry": round(entry, 6),
            "exit": 0,
            "margin": round(margin, 2),
            "pnl": 0,
            "funding": 0,
            "open_fee": 0,
            "close_fee": 0,
            "total_fees": 0,
            "reason": "OPEN",
            "time": time_now,
            "open_time": time_now,
            "close_time": "",
            "status": "open",
            "entry_price_display": f"${entry:.6f}" if entry < 1 else f"${entry:.4f}",
        })
    else:
        for t in reversed(trades):
            if t["symbol"] == symbol and t["reason"] == "OPEN":
                t["exit"] = round(exit_price, 6)
                t["pnl"] = round(pnl, 2)
                t["funding"] = round(funding, 4)
                close_fee = fees - t.get("open_fee", 0)
                t["close_fee"] = round(close_fee, 4)
                t["total_fees"] = round(fees, 4)
                t["reason"] = reason
                t["time"] = time_now
                t["close_time"] = time_now
                t["status"] = "closed"
                t["exit_price_display"] = f"${exit_price:.6f}" if exit_price < 1 else f"${exit_price:.4f}"
                if reason == "TP":
                    t["close_type"] = "TP"
                elif reason == "SL" or reason == "STOPPED":
                    t["close_type"] = "SL"
                elif "Trail" in reason:
                    t["close_type"] = "Trail"
                elif "LIQ" in reason or "Liquidated" in reason:
                    t["close_type"] = "Liq"
                elif pnl == 0 or abs(pnl) < 0.01:
                    t["close_type"] = "BU"
                else:
                    t["close_type"] = reason[:8]
                break
        else:
            close_fee = fees
            trade = {
                "date": date_str,
                "symbol": symbol,
                "side": side,
                "entry": round(entry, 6),
                "exit": round(exit_price, 6),
                "margin": round(margin, 2),
                "pnl": round(pnl, 2),
                "funding": round(funding, 4),
                "open_fee": 0,
                "close_fee": round(close_fee, 4),
                "total_fees": round(fees, 4),
                "reason": reason,
                "time": time_now,
                "open_time": time_now,
                "close_time": time_now,
                "status": "closed",
                "close_type": reason[:8],
                "entry_price_display": f"${entry:.6f}" if entry < 1 else f"${entry:.4f}",
                "exit_price_display": f"${exit_price:.6f}" if exit_price < 1 else f"${exit_price:.4f}",
            }
            trades.append(trade)
    if len(trades) > 500:
        trades = trades[-500:]
    save_trades(trades)
