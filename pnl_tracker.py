import json
import os
from datetime import datetime, timezone, timedelta

PNL_FILE = os.path.join(os.path.dirname(__file__), "pnl_history.json")
DAY_START_FILE = os.path.join(os.path.dirname(__file__), "day_start.json")


def load_pnl():
    try:
        with open(PNL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pnl(data):
    try:
        with open(PNL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_day_start():
    try:
        with open(DAY_START_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_day_start(data):
    try:
        with open(DAY_START_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_today_str():
    return (datetime.now(timezone.utc) + timedelta(hours=5)).strftime("%Y-%m-%d")


def get_or_set_day_start(equity):
    date_str = get_today_str()
    ds = load_day_start()
    if date_str not in ds:
        ds[date_str] = round(equity, 2)
        save_day_start(ds)
    return ds[date_str]


def record_day_end(date_str, realized_pnl, equity, trades, wins, losses):
    ds = load_day_start()
    start_eq = ds.get(date_str, 50.0)
    pnl_pct = (realized_pnl / start_eq * 100) if start_eq else 0
    data = load_pnl()
    data[date_str] = {
        "start_equity": start_eq,
        "pnl_usd": round(realized_pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "equity": round(equity, 2),
        "trades": trades,
        "wins": wins,
        "losses": losses,
    }
    save_pnl(data)


def get_pnl_history():
    return load_pnl()
