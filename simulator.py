import sys
import time
import logging
import json
from datetime import datetime, timezone
import os

from api_client import BitunixAPI
from strategy import analyze, generate_signal_mtf, load_stats, save_stats
from notifier import init_telegram, notify_trade_open, notify_trade_close, notify_status, notify_target_reached, notify_game_over, notify_daily_loss_limit
from ai_filter import evaluate_signal, learn_from_trade
from coin_selector import CoinSelector
from dashboard import start_dashboard
from pnl_tracker import record_day_end, get_pnl_history, get_or_set_day_start, get_today_str
from trade_log import log_trade
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, LIVE_MODE, API_KEY, API_SECRET, MARGIN_COIN

BALANCE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "balance.txt")
STATE_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("sim.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)])
log = logging.getLogger("bitunix_bot")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "SUIUSDT", "HYPEUSDT", "AVAXUSDT", "LINKUSDT",
    "WIFUSDT", "ARBUSDT", "OPUSDT", "APTUSDT", "NEARUSDT",
    "FILUSDT", "SANDUSDT", "MANAUSDT", "TRXUSDT", "DOTUSDT",
    "UNIUSDT", "TIAUSDT", "JUPUSDT", "FETUSDT", "SEIUSDT",
    "PYTHUSDT", "WLDUSDT", "INJUSDT", "ATOMUSDT", "LTCUSDT",
]

PD_SYMBOLS = [
    "1000BONKUSDT", "1000PEPEUSDT", "1000RATSUSDT", "1000SATSUSDT", "1000SHIBUSDT", "1INCHUSDT", "AAVEUSDT", "ACTUSDT",
    "ADAUSDT", "ALGOUSDT", "ALICEUSDT", "ALPINEUSDT", "ALTUSDT", "ANKRUSDT", "API3USDT", "APTUSDT",
    "ARBUSDT", "ARKMUSDT", "ARKUSDT", "ARPAUSDT", "ARUSDT", "ATOMUSDT", "AUCTIONUSDT", "AVAXUSDT",
    "AXSUSDT", "BANUSDT", "BATUSDT", "BCHUSDT", "BLZUSDT", "BNBUSDT", "BOMEUSDT", "BONDUSDT",
    "BRETTUSDT", "BSVUSDT", "BTCUSDT", "C98USDT", "CAKEUSDT", "CATIUSDT", "CELOUSDT", "CELRUSDT",
    "CFXUSDT", "CHILLGUYUSDT", "CHZUSDT", "CKBUSDT", "COMBOUSDT", "COMPUSDT", "COREUSDT", "COTIUSDT",
    "CRVUSDT", "CTKUSDT", "CTSIUSDT", "CVCUSDT", "CVXUSDT", "DARUSDT", "DASHUSDT", "DEXEUSDT",
    "DIAUSDT", "DOGEUSDT", "DOGSUSDT", "DOTUSDT", "DRIFTUSDT", "DUSKUSDT", "DYDXUSDT", "DYMUSDT",
    "EDUUSDT", "EGLDUSDT", "EIGENUSDT", "ENJUSDT", "ENSUSDT", "ETCUSDT", "ETHFIUSDT", "ETHUSDT",
    "FETUSDT", "FIDAUSDT", "FILUSDT", "FLOWUSDT", "FTMUSDT", "GALAUSDT", "GASUSDT", "GMTUSDT",
    "GOATUSDT", "GRTUSDT", "GTCUSDT", "HBARUSDT", "HEIUSDT", "HFTUSDT", "HIGHUSDT", "HIVEUSDT",
    "HOTUSDT", "HYPEUSDT", "ICXUSDT", "IDUSDT", "ILVUSDT", "IMXUSDT", "INJUSDT", "IOSTUSDT",
    "IOTAUSDT", "IOTXUSDT", "IOUSDT", "JSTUSDT", "JTOUSDT", "JUPUSDT", "KASUSDT", "KAVAUSDT",
    "KEYUSDT", "KLAYUSDT", "KNCUSDT", "KSMUSDT", "LDOUSDT", "LINKUSDT", "LITUSDT", "LOOMUSDT",
    "LPTUSDT", "LSKUSDT", "LTCUSDT", "LTOUSDT", "MANAUSDT", "MANTAUSDT", "MASKUSDT", "MATICUSDT",
    "MBLUSDT", "MDXUSDT", "MEMEUSDT", "MEUSDT", "MEWUSDT", "MINAUSDT", "MKRUSDT", "MLNUSDT",
    "MOODENGUSDT", "MOVRUSDT", "MTLUSDT", "NEARUSDT", "NEOUSDT", "NMRUSDT", "NOTUSDT", "OCEANUSDT",
    "OGUSDT", "ONDOUSDT", "ONEUSDT", "ONTUSDT", "OPUSDT", "ORBSUSDT", "ORDIUSDT", "PENDLEUSDT",
    "PIXELUSDT", "PNUTUSDT", "POPCATUSDT", "PORTALUSDT", "POWRUSDT", "PROMUSDT", "PUNDIXUSDT", "PYTHUSDT",
    "QNTUSDT", "QTUMUSDT", "RADUSDT", "RAREUSDT", "RAYUSDT", "RENDERUSDT", "RENUSDT", "RLCUSDT",
    "RNDRUSDT", "ROSEUSDT", "RUNEUSDT", "RVNUSDT", "SANDUSDT", "SEIUSDT", "SFPUSDT", "SKLUSDT",
    "SLPUSDT", "SNXUSDT", "SOLUSDT", "SPELLUSDT", "SSVUSDT", "STEEMUSDT", "STGUSDT", "STORJUSDT",
    "STRKUSDT", "STXUSDT", "SUIUSDT", "SUPERUSDT", "SUSHIUSDT", "TAOUSDT", "THETAUSDT", "TIAUSDT",
    "TLMUSDT", "TNSRUSDT", "TONUSDT", "TRBUSDT", "TRUMPUSDT", "TRXUSDT", "TURBOUSDT", "TWTUSDT",
    "UMAUSDT", "UNIUSDT", "VETUSDT", "VTHOUSDT", "WAVESUSDT", "WAXPUSDT", "WIFUSDT", "WLDUSDT",
    "WOOUSDT", "WUSDT", "XEMUSDT", "XLMUSDT", "XMRUSDT", "XRPUSDT", "XTZUSDT", "XVGUSDT",
    "XVSUSDT", "YFIUSDT", "YGGUSDT", "ZECUSDT", "ZENUSDT", "ZILUSDT", "ZKUSDT", "ZROUSDT",
    "ZRXUSDT",
]

MAX_POSITIONS = 3
POSITION_SIZE_PCT = 0.40
TARGET = 500.0
TAKER_FEE = 0.0006
MAKER_FEE = 0.0002
SPREAD_PCT = 0.0001
FUNDING_INTERVAL_CYCLES = 96
DAILY_LOSS_LIMIT_PCT = 0.30
MAX_LEVERAGE = 5
MAX_POSITION_RISK_PCT = 0.15
MAINTENANCE_MARGIN_RATE = 0.005
LIQUIDATION_THRESHOLD = 0.90
MIN_ORDER_USD = 0.50
BASE_SLIPPAGE = 0.0002
MAX_SLIPPAGE = 0.003
ORDER_REJECT_ATR_PCT = 4.0

LIQ_WARN_PCT = 0.55
LIQ_REDUCE_PCT = 0.70
LIQ_EMERGENCY_PCT = 0.85
LIQ_HEDGE_PCT = 0.45
MAX_DRAWDOWN_PCT = 0.25
TRAIL_STOP_ACTIVATE = 0.3
TRAIL_STOP_DISTANCE = 0.15

MAX_FUNDING_RATE = 0.01
MAX_HOLD_CYCLES = 60
FUNDING_CHECK_INTERVAL = 24

FUNDING_HARVEST_ENABLED = False
FUNDING_HARVEST_MIN_RATE = 0.006
FUNDING_HARVEST_SIZE_PCT = 0.15
FUNDING_HARVEST_LEVERAGE = 5
FUNDING_HARVEST_SL_PCT = 0.01
FUNDING_HARVEST_HOLD_CYCLES = 12
FUNDING_HARVEST_MAX_POSITIONS = 1

START_BALANCE = 50.0


def calc_slippage(atr_pct, notional_usd, vol_ratio=1.0):
    base = BASE_SLIPPAGE
    size_impact = min(notional_usd / 50000, 0.002)
    vol_impact = min((vol_ratio - 1) * 0.0005, 0.001) if vol_ratio > 1 else 0
    atr_impact = min(atr_pct / 100 * 0.3, 0.001)
    total = base + size_impact + vol_impact + atr_impact
    return min(total, MAX_SLIPPAGE)


def save_state(bot):
    try:
        eq = bot.balance + sum(p["margin"] + p.get("unrealized", 0) for p in bot.positions)
        realized = eq - bot.start_balance
        state = {"balance": bot.balance, "total_trades": bot.total_trades, "wins": bot.wins,
                 "losses": bot.losses, "total_fees": bot.total_fees, "start_balance": bot.start_balance,
                 "cycle_count": bot.cycle_count, "realized_pnl": realized,
                 "daily_reset_day": bot.daily_reset_day, "realized_pnl_today": bot.realized_pnl_today,
                 "day_start_eq": getattr(bot, 'day_start_eq', bot.start_balance),
                 "daily_loss": bot.daily_loss,
                  "positions": [{"symbol": p["symbol"], "side": p["side"], "entry": p["entry"],
                     "margin": p["margin"], "tp": p["tp"], "sl": p["sl"], "funding_rate": p["funding_rate"],
                     "total_funding_paid": p["total_funding_paid"], "open_fee": p["open_fee"],
                     "opened_cycle": p["opened_cycle"], "trail_active": p.get("trail_active", False),
                     "best_pnl": p.get("best_pnl", 0), "unrealized": p.get("unrealized", 0),
                     "current_price": p.get("current_price", 0)} for p in bot.positions]}
        with open(STATE_FILE, "w", encoding="utf-8") as f: json.dump(state, f, indent=2)
    except Exception: pass


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return None


class SimBot:
    def __init__(self):
        if LIVE_MODE:
            self.api = BitunixAPI(API_KEY, API_SECRET, "https://fapi.bitunix.com")
            print("  *** LIVE MODE - Real orders will be placed ***")
        else:
            self.api = BitunixAPI("", "", "https://fapi.bitunix.com")
            print("  SIMULATION MODE - No real orders")
        self.leverage = MAX_LEVERAGE
        self.balance = START_BALANCE
        self.positions = []
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_fees = 0
        self.start_balance = START_BALANCE
        self.target = TARGET
        self.running = True
        self.cycle_count = 0
        self.start_time = time.time()
        self.closed_symbols = {}
        self.daily_loss = 0.0
        from datetime import timezone, timedelta
        self.daily_reset_day = (datetime.now(timezone.utc) + timedelta(hours=5)).day - 1
        self.realized_pnl_today = 0.0
        self.first_cycle = True
        self.day_start_eq = self.balance
        self.symbol = "BTCUSDT"
        init_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.coin_selector = CoinSelector(self.api)
        self.last_signals = []
        state = load_state()
        if state:
            self.balance = state.get("balance", START_BALANCE)
            self.total_trades = state.get("total_trades", 0)
            self.wins = state.get("wins", 0)
            self.losses = state.get("losses", 0)
            self.total_fees = state.get("total_fees", 0)
            self.start_balance = state.get("start_balance", START_BALANCE)
            self.cycle_count = state.get("cycle_count", 0)
            self.realized_pnl_today = state.get("realized_pnl_today", 0.0)
            self.daily_reset_day = state.get("daily_reset_day", self.daily_reset_day)
            self.day_start_eq = state.get("day_start_eq", self.balance)
            self.daily_loss = 0.0
            for p in state.get("positions", []):
                p["unrealized"] = 0; p["total_funding_paid"] = p.get("total_funding_paid", 0)
                p["trail_active"] = p.get("trail_active", False); p["best_pnl"] = p.get("best_pnl", 0)
                self.positions.append(p)
            eq = self.balance + sum(p["margin"] + p.get("unrealized", 0) for p in self.positions)
            saved_start = state.get("start_balance", START_BALANCE)
            self.start_balance = saved_start
            print(f"  Resumed: ${self.balance:.2f} | {len(self.positions)} pos | Start: ${saved_start:.2f}")

    def equity(self):
        return self.balance + sum(p["margin"] + p.get("unrealized", 0) for p in self.positions)

    def get_klines(self, symbol, interval="5m", limit=100):
        try:
            resp = self.api._get("/api/v1/futures/market/kline", {"symbol": symbol, "interval": interval, "limit": str(limit)})
            if resp.get("code") == 0: return resp.get("data", [])
        except Exception: pass
        return []

    def open_position(self, symbol, side, price, analysis):
        if self.balance < 1.0: return
        total_margin = self.balance * POSITION_SIZE_PCT
        margin = total_margin / MAX_POSITIONS
        if margin < 1.0: return

        atr_pct = analysis.get("atr_pct", 1.0)
        vol_ratio = analysis.get("vol_ratio", 1.0)

        if atr_pct > ORDER_REJECT_ATR_PCT:
            print(f"  REJECTED {symbol}: ATR {atr_pct:.1f}% too high")
            return

        notional = margin * self.leverage
        if notional < MIN_ORDER_USD:
            return

        slippage = calc_slippage(atr_pct, notional, vol_ratio)
        entry_price = price * (1 + slippage) if side == "LONG" else price * (1 - slippage)

        sl_pct = min(max(atr_pct * 1.5, 1.5) / 100, 0.03)
        max_margin_by_risk = (self.balance * MAX_POSITION_RISK_PCT) / (sl_pct * self.leverage) if sl_pct > 0 else margin
        if margin > max_margin_by_risk:
            margin = max_margin_by_risk
            if margin < 1.0: return
            notional = margin * self.leverage

        tp_pct = min(max(atr_pct * 2.5, 2.5) / 100, 0.05)
        sig = max(8, len(str(entry_price).rstrip('0').split('.')[-1]) + 2) if '.' in str(entry_price) else 8
        if side == "LONG":
            tp = round(entry_price * (1 + tp_pct), sig)
            sl = round(entry_price * (1 - sl_pct), sig)
        else:
            tp = round(entry_price * (1 - tp_pct), sig)
            sl = round(entry_price * (1 + sl_pct), sig)

        funding_rate = 0
        try:
            resp = self.api._get("/api/v1/futures/market/funding_rate", {"symbol": symbol})
            if resp.get("code") == 0:
                data = resp.get("data", {})
                if isinstance(data, dict): funding_rate = float(data.get("fundingRate", 0))
        except Exception: pass

        if abs(funding_rate) > MAX_FUNDING_RATE:
            print(f"  REJECTED {symbol}: funding {funding_rate*100:.3f}% > {MAX_FUNDING_RATE*100:.3f}%")
            return

        qty = round(notional / price, 6)
        real_entry = entry_price

        if LIVE_MODE:
            try:
                self.api.change_leverage(symbol, self.leverage, MARGIN_COIN)
            except Exception as e:
                print(f"  Leverage set error: {e}")

            api_side = "BUY" if side == "LONG" else "SELL"
            resp = self.api.place_order(
                symbol=symbol, side=api_side, trade_side="OPEN",
                order_type="MARKET", qty=qty, tp_price=tp, sl_price=sl,
            )
            if resp.get("code") != 0:
                print(f"  ORDER FAILED {symbol}: {resp.get('msg', resp)}")
                return
            try:
                order_data = resp.get("data", {})
                if isinstance(order_data, dict) and order_data.get("avgPrice"):
                    real_entry = float(order_data["avgPrice"])
            except Exception:
                pass
            print(f"  REAL ORDER placed: {symbol} {side} qty={qty}")
        else:
            real_entry = entry_price

        open_fee = notional * TAKER_FEE
        slippage_cost = notional * abs(real_entry - price) / price if price > 0 else notional * slippage
        self.balance -= margin + open_fee + slippage_cost
        self.total_fees += open_fee

        pos = {"symbol": symbol, "side": side, "entry": real_entry, "margin": margin,
               "tp": tp, "sl": sl, "unrealized": 0, "opened_cycle": self.cycle_count,
               "funding_rate": funding_rate, "total_funding_paid": 0, "open_fee": open_fee,
               "trail_active": False, "best_pnl": 0.0, "last_funding_cycle": self.cycle_count,
               "slippage_paid": slippage_cost, "qty": qty}
        self.positions.append(pos)
        self.total_trades += 1
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"  >>> [{now}] OPEN {side} {symbol} | ${real_entry:.4f} | TP: ${tp} | SL: ${sl} | Margin: ${margin:.2f} | Slip: {slippage*100:.3f}%")
        notify_trade_open(symbol, side, real_entry, tp, sl, margin)
        log_trade(symbol, side, real_entry, real_entry, margin, 0, "OPEN", now)

    def close_position(self, idx, price, reason=""):
        pos = self.positions[idx]

        if LIVE_MODE:
            try:
                resp = self.api.flash_close_position(pos["symbol"])
                if resp.get("code") != 0:
                    print(f"  CLOSE FAILED {pos['symbol']}: {resp.get('msg', resp)}")
                    return
                print(f"  REAL CLOSE placed: {pos['symbol']}")
            except Exception as e:
                print(f"  CLOSE ERROR {pos['symbol']}: {e}")
                return

        if reason == "LIQUIDATED":
            net_pnl = -pos["margin"]
            exit_price = price
            close_fee = 0
            self.balance += net_pnl
        else:
            notional = pos["margin"] * self.leverage
            atr_pct = 1.0
            try:
                klines = self.get_klines(pos["symbol"], "5m", 20)
                if klines:
                    closes = [float(k["close"]) for k in klines]
                    highs = [float(k["high"]) for k in klines]
                    lows = [float(k["low"]) for k in klines]
                    if len(closes) > 14:
                        trs = []
                        for i in range(1, len(closes)):
                            tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
                            trs.append(tr)
                        atr_val = sum(trs[-14:]) / 14
                        atr_pct = atr_val / closes[-1] * 100 if closes[-1] > 0 else 1.0
            except Exception: pass

            slippage = calc_slippage(atr_pct, notional)
            exit_price = price * (1 - slippage) if pos["side"] == "LONG" else price * (1 + slippage)
            pnl_pct = ((exit_price - pos["entry"]) / pos["entry"]) if pos["side"] == "LONG" else ((pos["entry"] - exit_price) / pos["entry"])
            pnl_usd = pos["margin"] * self.leverage * pnl_pct
            close_fee = notional * TAKER_FEE
            slippage_cost = notional * slippage
            net_pnl = pnl_usd - close_fee - slippage_cost - pos["total_funding_paid"]
            self.balance += pos["margin"] + net_pnl
            self.total_fees += close_fee
        if net_pnl > 0: self.wins += 1
        else:
            self.losses += 1
            self.daily_loss += abs(net_pnl)
        self.realized_pnl_today += net_pnl

        try:
            learn_from_trade({"signal": pos["side"], "score": 5, "confirmations": 5, "threshold": 4}, {}, net_pnl > 0)
        except Exception: pass

        stats = load_stats()
        if pnl_pct > 0:
            stats["wins"] = stats.get("wins", 0) + 1
            sw = stats.get("avg_win", 0)
            stats["avg_win"] = (sw * (stats["wins"] - 1) + pnl_pct * 100) / stats["wins"]
        else:
            stats["losses"] = stats.get("losses", 0) + 1
            sl = stats.get("avg_loss", 0)
            stats["avg_loss"] = (sl * (stats["losses"] - 1) + pnl_pct * 100) / stats["losses"]
        stats["total_pnl"] = stats.get("total_pnl", 0) + pnl_pct * 100
        stats["best_trade"] = max(stats.get("best_trade", 0), pnl_pct * 100)
        stats["worst_trade"] = min(stats.get("worst_trade", 0), pnl_pct * 100)
        if pos["symbol"] not in stats.get("patterns", {}): stats["patterns"][pos["symbol"]] = {"w": 0, "l": 0}
        if pnl_pct > 0: stats["patterns"][pos["symbol"]]["w"] += 1
        else: stats["patterns"][pos["symbol"]]["l"] += 1
        save_stats(stats)

        cd = 10 if net_pnl > 0 else 30
        self.closed_symbols[pos["symbol"]] = (self.cycle_count, cd)
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"  >>> [{now}] CLOSE {pos['side']} {pos['symbol']} | ${pos['entry']:.4f} -> ${exit_price:.4f} | PnL: ${net_pnl:+.2f} ({pnl_pct*100:+.1f}%) | Bal: ${self.balance:.2f} | {reason}")
        if pos.get("is_funding_harvest"):
            funding_earned = abs(pos.get("total_funding_paid", 0))
            print(f"  FUNDING EARNED: ${funding_earned:.2f} | Fees: ${pos.get('open_fee', 0) + close_fee:.2f} | Net: ${funding_earned - pos.get('open_fee', 0) - close_fee:+.2f}")
        notify_trade_close(pos['symbol'], pos['side'], pos['entry'], exit_price, net_pnl, reason)
        log_trade(pos['symbol'], pos['side'], pos['entry'], exit_price, pos['margin'], net_pnl, reason, now, funding=pos.get('total_funding_paid', 0), fees=pos.get('open_fee', 0) + close_fee)
        self.positions.pop(idx)
        save_state(self)

    def check_smart_exit(self):
        to_close = []
        for i, pos in enumerate(self.positions):
            klines = self.get_klines(pos["symbol"], "1m", 20)
            if not klines: continue
            price = float(klines[-1]["close"])
            cycles_held = self.cycle_count - pos["opened_cycle"]
            if pos["side"] == "LONG":
                pnl = (price - pos["entry"]) / pos["entry"] * self.leverage
            else:
                pnl = (pos["entry"] - price) / pos["entry"] * self.leverage
            pos["unrealized"] = pnl / self.leverage * pos["margin"]
            pos["current_price"] = price

            maintenance_margin = pos["margin"] * MAINTENANCE_MARGIN_RATE * self.leverage
            if pos["unrealized"] < 0 and abs(pos["unrealized"]) >= pos["margin"] - maintenance_margin:
                to_close.append((i, price, "LIQUIDATED"))
                continue

            if cycles_held >= MAX_HOLD_CYCLES:
                to_close.append((i, price, f"MAX HOLD {cycles_held} cycles"))
                continue

            fr = abs(pos.get("funding_rate", 0))
            if fr > MAX_FUNDING_RATE and cycles_held >= FUNDING_CHECK_INTERVAL:
                funding_cost_8h = pos["margin"] * self.leverage * fr
                if pos["unrealized"] < funding_cost_8h:
                    to_close.append((i, price, f"HIGH FUNDING {fr*100:.3f}% > {MAX_FUNDING_RATE*100:.3f}%"))
                    continue

            total_funding = abs(pos.get("total_funding_paid", 0))
            if total_funding > pos["margin"] * 0.5 and pos["unrealized"] < pos["margin"] * 0.3:
                to_close.append((i, price, f"FUNDING EATEN {total_funding:.2f} > 50% margin"))
                continue

            cycles_since_funding = self.cycle_count - pos.get("last_funding_cycle", pos["opened_cycle"])
            if cycles_since_funding >= FUNDING_INTERVAL_CYCLES:
                try:
                    resp = self.api._get("/api/v1/futures/market/funding_rate", {"symbol": pos["symbol"]})
                    if resp.get("code") == 0:
                        data = resp.get("data", {})
                        if isinstance(data, dict):
                            pos["funding_rate"] = float(data.get("fundingRate", 0))
                except Exception: pass

                fr = pos.get("funding_rate", 0)
                funding_cost = pos["margin"] * self.leverage * abs(fr)
                if pos["side"] == "LONG":
                    pos["total_funding_paid"] = pos.get("total_funding_paid", 0) + funding_cost if fr > 0 else pos.get("total_funding_paid", 0) - funding_cost
                else:
                    pos["total_funding_paid"] = pos.get("total_funding_paid", 0) + funding_cost if fr < 0 else pos.get("total_funding_paid", 0) - funding_cost
                pos["last_funding_cycle"] = self.cycle_count

            if not pos.get("trail_active") and pnl >= 0.4:
                pos["trail_active"] = True
                if pos["side"] == "LONG":
                    pos["sl"] = pos["entry"] * 1.002
                else:
                    pos["sl"] = pos["entry"] * 0.998

            if pos.get("trail_active") and pnl >= 0.6:
                trail_dist = 0.003
                if pos["side"] == "LONG":
                    new_sl = price * (1 - trail_dist)
                    if new_sl > pos["sl"]: pos["sl"] = new_sl
                else:
                    new_sl = price * (1 + trail_dist)
                    if new_sl < pos["sl"]: pos["sl"] = new_sl

            if pos.get("trail_active") and pos.get("best_pnl", 0) > 0.6 and pnl < pos.get("best_pnl", 0) * 0.30:
                to_close.append((i, price, f"Trail exit peak:{pos['best_pnl']:.1f}% now:{pnl:.1f}%"))
                continue

            hit = False
            reason = ""
            if pos["side"] == "LONG":
                if price >= pos["tp"]: hit = True; reason = "TP"
                elif price <= pos["sl"]:
                    if pos.get("trail_active") and pos["sl"] > pos["entry"]:
                        hit = True; reason = "Trail"
                    else:
                        hit = True; reason = "SL"
            else:
                if price <= pos["tp"]: hit = True; reason = "TP"
                elif price >= pos["sl"]:
                    if pos.get("trail_active") and pos["sl"] < pos["entry"]:
                        hit = True; reason = "Trail"
                    else:
                        hit = True; reason = "SL"
            if hit:
                to_close.append((i, price, reason))
                continue

            if cycles_held >= 5:
                if pnl > 1.0:
                    k5 = self.get_klines(pos["symbol"], "5m", 30)
                    if k5:
                        a = analyze(k5)
                        if (pos["side"] == "LONG" and a["rsi"] > 75) or (pos["side"] == "SHORT" and a["rsi"] < 25):
                            to_close.append((i, price, f"RSI exit +{pnl:.1f}%"))
                            continue
                        pd = a["pump_dump"]
                        if pos["side"] == "LONG" and pd["dump"]:
                            to_close.append((i, price, f"Dump cut +{pnl:.1f}%"))
                        elif pos["side"] == "SHORT" and pd["pump"]:
                            to_close.append((i, price, f"Pump cut +{pnl:.1f}%"))
                if pnl < -0.6 and cycles_held >= 8:
                    k5 = self.get_klines(pos["symbol"], "5m", 30)
                    if k5:
                        a = analyze(k5)
                        pd = a["pump_dump"]
                        if pos["side"] == "LONG" and pd["dump"]:
                            to_close.append((i, price, f"Dump cut {pnl:.1f}%"))
                        elif pos["side"] == "SHORT" and pd["pump"]:
                            to_close.append((i, price, f"Pump cut {pnl:.1f}%"))

                if cycles_held >= 30 and abs(pnl) < 0.3:
                    to_close.append((i, price, f"STAGNANT {cycles_held}c pnl:{pnl:.1f}%"))
                    continue

        for idx, price, reason in reversed(to_close):
            self.close_position(idx, price, reason)

    def refresh_unrealized(self):
        for pos in self.positions:
            try:
                klines = self.get_klines(pos["symbol"], "1m", 5)
                if not klines: continue
                price = float(klines[-1]["close"])
                if pos["side"] == "LONG":
                    pnl_pct = (price - pos["entry"]) / pos["entry"]
                else:
                    pnl_pct = (pos["entry"] - price) / pos["entry"]
                pos["unrealized"] = pnl_pct * pos["margin"] * self.leverage
                pos["current_price"] = price
            except Exception:
                pass

    def calc_liquidation_price(self, pos):
        entry = pos["entry"]
        margin_ratio = MAINTENANCE_MARGIN_RATE
        if pos["side"] == "LONG":
            liq = entry * (1 - (1 / self.leverage) + margin_ratio)
        else:
            liq = entry * (1 + (1 / self.leverage) - margin_ratio)
        return liq

    def get_margin_usage(self, pos):
        if pos["margin"] <= 0: return 0
        return abs(pos["unrealized"]) / pos["margin"]

    def check_liquidation_protection(self):
        to_close = []
        to_reduce = []
        for i, pos in enumerate(self.positions):
            usage = self.get_margin_usage(pos)
            price = pos.get("current_price", pos["entry"])
            liq_price = self.calc_liquidation_price(pos)

            if usage >= LIQ_EMERGENCY_PCT:
                to_close.append((i, price, f"LIQ PROTECT emergency {usage*100:.0f}%"))
                print(f"  !!! EMERGENCY CLOSE {pos['symbol']} margin usage {usage*100:.1f}% liq:${liq_price:.6f}")
            elif usage >= LIQ_REDUCE_PCT:
                reduce_pct = 0.5
                new_margin = pos["margin"] * (1 - reduce_pct)
                if new_margin >= 1.0:
                    to_reduce.append((i, price, reduce_pct, f"LIQ PROTECT reduce {usage*100:.0f}%"))
                    print(f"  !!! REDUCE {pos['symbol']} by {reduce_pct*100:.0f}% margin usage {usage*100:.1f}% liq:${liq_price:.6f}")
                else:
                    to_close.append((i, price, f"LIQ PROTECT forced close {usage*100:.0f}%"))
                    print(f"  !!! FORCED CLOSE {pos['symbol']} margin too small after reduce")
            elif usage >= LIQ_WARN_PCT:
                if not pos.get("emergency_sl"):
                    if pos["side"] == "LONG":
                        pos["emergency_sl"] = price * 0.997
                    else:
                        pos["emergency_sl"] = price * 1.003
                    print(f"  ! WARN {pos['symbol']} margin usage {usage*100:.1f}% emergency SL set")

            if pos.get("emergency_sl"):
                if pos["side"] == "LONG" and price <= pos["emergency_sl"]:
                    to_close.append((i, price, f"Emergency SL {usage*100:.0f}%"))
                elif pos["side"] == "SHORT" and price >= pos["emergency_sl"]:
                    to_close.append((i, price, f"Emergency SL {usage*100:.0f}%"))

            if usage >= LIQ_HEDGE_PCT and not pos.get("hedged"):
                hedge_margin = pos["margin"] * 0.3
                if hedge_margin >= 1.0 and self.balance >= hedge_margin + 1:
                    hedge_side = "SHORT" if pos["side"] == "LONG" else "LONG"
                    hedge_qty = round(hedge_margin * self.leverage / price, 6)
                    if LIVE_MODE:
                        try:
                            api_side = "BUY" if hedge_side == "LONG" else "SELL"
                            resp = self.api.place_order(
                                symbol=pos["symbol"], side=api_side, trade_side="OPEN",
                                order_type="MARKET", qty=hedge_qty,
                            )
                            if resp.get("code") == 0:
                                print(f"  ! HEDGE OPENED {pos['symbol']} {hedge_side} qty={hedge_qty}")
                            else:
                                print(f"  ! HEDGE FAILED {pos['symbol']}: {resp.get('msg', resp)}")
                        except Exception as e:
                            print(f"  ! HEDGE ERROR {pos['symbol']}: {e}")
                    else:
                        print(f"  ! HEDGE {pos['symbol']} {hedge_side} margin=${hedge_margin:.2f} usage={usage*100:.1f}%")
                    pos["hedged"] = True

        for i, price, reason in reversed(to_close):
            self.close_position(i, price, reason)
        for i, price, reduce_pct, reason in reversed(to_reduce):
            self.reduce_position(i, reduce_pct)

    def reduce_position(self, idx, reduce_pct):
        pos = self.positions[idx]
        reduce_margin = pos["margin"] * reduce_pct
        notional_reduce = reduce_margin * self.leverage
        close_fee = notional_reduce * TAKER_FEE
        slippage = calc_slippage(1.0, notional_reduce)
        price = pos.get("current_price", pos["entry"])

        if LIVE_MODE:
            reduce_qty = round(notional_reduce / price, 6)
            try:
                close_side = "SELL" if pos["side"] == "LONG" else "BUY"
                resp = self.api.place_order(
                    symbol=pos["symbol"], side=close_side, trade_side="CLOSE",
                    order_type="MARKET", qty=reduce_qty,
                )
                if resp.get("code") != 0:
                    print(f"  REDUCE FAILED {pos['symbol']}: {resp.get('msg', resp)}")
                    return
            except Exception as e:
                print(f"  REDUCE ERROR {pos['symbol']}: {e}")
                return

        if pos["side"] == "LONG":
            exit_price = price * (1 - slippage)
            pnl_pct = (exit_price - pos["entry"]) / pos["entry"]
        else:
            exit_price = price * (1 + slippage)
            pnl_pct = (pos["entry"] - exit_price) / pos["entry"]

        pnl_usd = reduce_margin * self.leverage * pnl_pct
        net_pnl = pnl_usd - close_fee
        self.balance += reduce_margin + net_pnl
        self.total_fees += close_fee

        pos["margin"] -= reduce_margin
        if pos["side"] == "LONG":
            pos["tp"] = round(pos["entry"] * 1.02, 4)
            pos["sl"] = round(pos["entry"] * 0.99, 4)
        else:
            pos["tp"] = round(pos["entry"] * 0.98, 4)
            pos["sl"] = round(pos["entry"] * 1.01, 4)
        pos.pop("emergency_sl", None)

        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"  >>> [{now}] REDUCE {pos['side']} {pos['symbol']} by {reduce_pct*100:.0f}% | PnL: ${net_pnl:+.2f} | New margin: ${pos['margin']:.2f}")
        log_trade(pos["symbol"], pos["side"], pos["entry"], exit_price, reduce_margin, net_pnl, "REDUCE", now, funding=0, fees=close_fee)

    def check_funding_harvest(self):
        if not FUNDING_HARVEST_ENABLED:
            return
        if len(self.positions) >= MAX_POSITIONS:
            return
        funding_positions = [p for p in self.positions if p.get("is_funding_harvest")]
        if len(funding_positions) >= FUNDING_HARVEST_MAX_POSITIONS:
            for pos in funding_positions:
                cycles_held = self.cycle_count - pos["opened_cycle"]
                if cycles_held >= FUNDING_HARVEST_HOLD_CYCLES:
                    try:
                        klines = self.get_klines(pos["symbol"], "1m", 5)
                        if klines:
                            price = float(klines[-1]["close"])
                            if pos["side"] == "LONG":
                                pnl = (price - pos["entry"]) / pos["entry"] * FUNDING_HARVEST_LEVERAGE
                            else:
                                pnl = (pos["entry"] - price) / pos["entry"] * FUNDING_HARVEST_LEVERAGE
                            pos["unrealized"] = pnl / FUNDING_HARVEST_LEVERAGE * pos["margin"]
                            pos["current_price"] = price
                            funding_earned = -pos.get("total_funding_paid", 0) if pos.get("total_funding_paid", 0) < 0 else 0
                            price_pnl = pos["unrealized"]
                            total_profit = funding_earned + price_pnl - pos.get("open_fee", 0)
                            if pnl < -FUNDING_HARVEST_SL_PCT * FUNDING_HARVEST_LEVERAGE:
                                reason = f"FUNDING SL ${total_profit:+.2f} (fund:${funding_earned:.2f} price:${price_pnl:+.2f})"
                                self.close_position(self.positions.index(pos), price, reason)
                            elif cycles_held >= FUNDING_HARVEST_HOLD_CYCLES + 6:
                                reason = f"FUNDING DONE ${total_profit:+.2f} (fund:${funding_earned:.2f} price:${price_pnl:+.2f})"
                                self.close_position(self.positions.index(pos), price, reason)
                    except Exception:
                        pass
            return

        from datetime import timezone, timedelta
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour
        minute = now_utc.minute
        minutes_to_funding = None
        if hour < 8:
            minutes_to_funding = (8 - hour) * 60 - minute
        elif hour < 16:
            minutes_to_funding = (16 - hour) * 60 - minute
        else:
            minutes_to_funding = (24 - hour) * 60 + (0 - minute)

        if minutes_to_funding is None or minutes_to_funding > 30 or minutes_to_funding < 0:
            return

        top_symbols = self._scan_funding_rates()
        for symbol, rate, direction in top_symbols:
            if len(self.positions) >= MAX_POSITIONS:
                break
            if any(p["symbol"] == symbol for p in self.positions):
                continue
            if symbol in self.closed_symbols:
                last_close, cd = self.closed_symbols[symbol]
                if self.cycle_count - last_close < cd:
                    continue

            try:
                klines = self.get_klines(symbol, "5m", 50)
                if not klines or len(klines) < 30:
                    continue
                price = float(klines[-1]["close"])

                available = self.balance * FUNDING_HARVEST_SIZE_PCT
                if available < 2.0:
                    continue

                notional = available * FUNDING_HARVEST_LEVERAGE
                margin = available
                fee = notional * TAKER_FEE
                self.balance -= margin + fee
                self.total_fees += fee

                if direction == "LONG":
                    entry_price = price * (1 + BASE_SLIPPAGE)
                    tp = round(entry_price * 1.003, 6)
                    sl = round(entry_price * (1 - FUNDING_HARVEST_SL_PCT), 6)
                else:
                    entry_price = price * (1 - BASE_SLIPPAGE)
                    tp = round(entry_price * 0.997, 6)
                    sl = round(entry_price * (1 + FUNDING_HARVEST_SL_PCT), 6)

                expected_funding = notional * abs(rate)
                pos = {
                    "symbol": symbol, "side": direction, "entry": entry_price,
                    "margin": margin, "tp": tp, "sl": sl, "unrealized": 0,
                    "opened_cycle": self.cycle_count, "funding_rate": rate,
                    "total_funding_paid": 0, "open_fee": fee,
                    "trail_active": False, "best_pnl": 0.0,
                    "last_funding_cycle": self.cycle_count,
                    "slippage_paid": 0, "qty": round(notional / price, 6),
                    "is_funding_harvest": True,
                }
                self.positions.append(pos)
                self.total_trades += 1
                now = datetime.now(timezone.utc).strftime("%H:%M:%S")
                print(f"  >>> [{now}] FUNDING {direction} {symbol} | rate: {rate*100:.3f}% | Entry: ${entry_price:.6f} | Margin: ${margin:.2f} | Expected: ${expected_funding:.2f}")
                log_trade(symbol, direction, entry_price, entry_price, margin, 0, "FUNDING OPEN", now, funding=0, fees=fee)
                break
            except Exception:
                pass

    def _scan_funding_rates(self):
        results = []
        scan_symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT",
            "1000PEPEUSDT", "1000BONKUSDT", "1000SHIBUSDT", "WIFUSDT", "BOMEUSDT",
            "MEMEUSDT", "SUIUSDT", "AVAXUSDT", "LINKUSDT", "ARBUSDT",
            "OPUSDT", "FILUSDT", "NEARUSDT", "APTUSDT", "DOTUSDT",
            "ADAUSDT", "TRXUSDT", "TONUSDT", "SANDUSDT", "MANAUSDT",
            "FETUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT", "JUPUSDT",
            "PYTHUSDT", "WLDUSDT", "STRKUSDT", "STXUSDT", "PENDLEUSDT",
            "ORDIUSDT", "RNDRUSDT", "RENDERUSDT", "MATICUSDT", "ATOMUSDT",
            "NEOUSDT", "ETCUSDT", "BCHUSDT", "LTCUSDT", "UNIUSDT",
            "AAVEUSDT", "SNXUSDT", "CRVUSDT", "DYDXUSDT", "GMXUSDT",
            "HYPEUSDT", "TRUMPUSDT", "PNUTUSDT", "MOODENGUSDT", "GOATUSDT",
            "CHILLGUYUSDT", "BRETTUSDT", "MEWUSDT", "TURBOUSDT", "CATIUSDT",
            "EIGENUSDT", "KASUSDT", "HBARUSDT", "XLMUSDT", "VETUSDT",
            "THETAUSDT", "GRTUSDT", "FTMUSDT", "ALGOUSDT", "RUNEUSDT",
        ]
        for symbol in scan_symbols:
            try:
                resp = self.api._get("/api/v1/futures/market/funding_rate", {"symbol": symbol})
                if resp.get("code") == 0:
                    data = resp.get("data", {})
                    if isinstance(data, dict):
                        rate = float(data.get("fundingRate", 0))
                        if abs(rate) >= FUNDING_HARVEST_MIN_RATE:
                            direction = "LONG" if rate < 0 else "SHORT"
                            results.append((symbol, rate, direction))
            except Exception:
                pass
            time.sleep(0.05)
        results.sort(key=lambda x: abs(x[1]), reverse=True)
        return results[:3]

    def check_max_drawdown(self):
        eq = self.equity()
        drawdown = (self.start_balance - eq) / self.start_balance if self.start_balance > 0 else 0
        if drawdown >= MAX_DRAWDOWN_PCT:
            print(f"\n*** MAX DRAWDOWN {drawdown*100:.1f}% >= {MAX_DRAWDOWN_PCT*100:.0f}% - PAUSING ***")
            notify_daily_loss_limit(drawdown * self.start_balance)
            return True
        return False

    def scan_pump_dump(self):
        results = []
        def _scan_one(sym):
            try:
                klines = self.get_klines(sym, "5m", 30)
                if len(klines) < 20: return None
                price = float(klines[-1]["close"])
                analysis = analyze(klines)
                pd = analysis["pump_dump"]
                if pd["pump"] or pd["dump"]:
                    signal = generate_signal_mtf({"price": price, "4h": None, "1h": analysis, "5m": analysis})
                    if signal["signal"] != "HOLD":
                        return (sym, price, signal, analysis)
            except Exception: pass
            return None

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=25) as ex:
            for r in ex.map(_scan_one, PD_SYMBOLS):
                if r: results.append(r)
        return results

    def scan_all(self):
        results = []
        symbols = self.coin_selector.select_coins(self.cycle_count)

        def _scan_one(sym):
            try:
                k4h = self.get_klines(sym, "4h", 100)
                k1h = self.get_klines(sym, "1h", 150)
                k5m = self.get_klines(sym, "5m", 100)
                if len(k1h) < 30: return None
                price = float(k5m[-1]["close"]) if k5m else float(k1h[-1]["close"])
                a_4h = analyze(k4h) if len(k4h) >= 30 else None
                a_1h = analyze(k1h)
                a_5m = analyze(k5m) if len(k5m) >= 30 else None
                mtf = {"price": price, "4h": a_4h, "1h": a_1h, "5m": a_5m}
                signal = generate_signal_mtf(mtf)
                return (sym, price, signal, mtf)
            except Exception:
                return None

        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=20) as ex:
            for r in ex.map(_scan_one, symbols):
                if r: results.append(r)
        return results

    def run(self):
        mode = "LIVE" if LIVE_MODE else "SIMULATION"
        print("=" * 70)
        print(f"  BITUNIX BOT v13 - {mode} MODE")
        print(f"  Start: ${self.start_balance:.0f} -> Target: ${self.target:.0f} | {self.leverage}x")
        print(f"  {POSITION_SIZE_PCT*100:.0f}% total across {MAX_POSITIONS} pos | Taker {TAKER_FEE*100:.2f}%")
        print(f"  Dynamic slippage | Real funding | ATR reject >{ORDER_REJECT_ATR_PCT}%")
        print(f"  LIQ protect: warn>{LIQ_WARN_PCT*100:.0f}% reduce>{LIQ_REDUCE_PCT*100:.0f}% emergency>{LIQ_EMERGENCY_PCT*100:.0f}%")
        print(f"  4H trend | 1H levels | 5M entry | AI filter | Auto-learn")
        print("=" * 70)

        if LIVE_MODE:
            try:
                resp = self.api.get_account(MARGIN_COIN)
                if resp.get("code") == 0:
                    data = resp.get("data", {})
                    if isinstance(data, list): data = data[0] if data else {}
                    real_bal = float(data.get("available", 0))
                    real_margin = float(data.get("margin", 0))
                    print(f"  API OK | Available: ${real_bal:.2f} | Margin: ${real_margin:.2f} | Total: ${real_bal+real_margin:.2f}")
                    self.balance = real_bal
                else:
                    print(f"  API ERROR: {resp}")
                    print("  Check your API keys in config.py!")
                    return
            except Exception as e:
                print(f"  API CONNECTION FAILED: {e}")
                return

        start_dashboard(self)
        self.daily_paused = False

        while self.running:
            try:
                self.cycle_count += 1
                elapsed_min = (time.time() - self.start_time) / 60

                eq = self.equity()
                from datetime import timezone, timedelta
                now_tz = datetime.now(timezone.utc) + timedelta(hours=5)
                today = now_tz.day
                today_str = now_tz.strftime("%Y-%m-%d")
                if today != self.daily_reset_day:
                    if not self.first_cycle or self.realized_pnl_today != 0:
                        yesterday_dt = now_tz - timedelta(days=1)
                        yesterday_str = yesterday_dt.strftime("%Y-%m-%d")
                        from pnl_tracker import load_pnl as _lpnl
                        existing = _lpnl()
                        if yesterday_str not in existing:
                            record_day_end(yesterday_str, self.realized_pnl_today, eq, self.total_trades, self.wins, self.losses)
                            print(f"  Day {yesterday_str} PnL: ${self.realized_pnl_today:+.2f}")
                    self.daily_loss = 0.0
                    self.realized_pnl_today = 0.0
                    self.daily_reset_day = today
                    self.first_cycle = False
                    self.day_start_eq = eq
                    self.daily_paused = False
                    get_or_set_day_start(eq)

                if self.daily_loss >= eq * DAILY_LOSS_LIMIT_PCT and not self.daily_paused:
                    self.daily_paused = True
                    print(f"\n*** DAILY LOSS LIMIT ${self.daily_loss:.2f} - pausing new trades ***")
                    notify_daily_loss_limit(self.daily_loss)

                if not self.daily_paused:
                    self.check_funding_harvest()

                self.check_smart_exit()
                self.check_liquidation_protection()

                if eq >= self.target:
                    print(f"\n*** TARGET REACHED in {elapsed_min:.0f} min! ***")
                    notify_target_reached(eq, self.target)
                    self.running = False; break
                if self.balance < 1.0 and not self.positions:
                    print(f"\n*** GAME OVER in {elapsed_min:.0f} min ***")
                    notify_game_over(self.balance)
                    self.running = False; break

                results = self.scan_all()
                pd_results = self.scan_pump_dump()
                seen = {r[0] for r in results}
                for r in pd_results:
                    if r[0] not in seen:
                        results.append(r)
                now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                pnl_pct = (eq - self.start_balance) / self.start_balance * 100
                progress = min(eq / self.target * 100, 100)
                filled = int(20 * eq / self.target)
                bar = "#" * filled + "-" * (20 - filled)
                wr = f"{self.wins/self.total_trades*100:.0f}%" if self.total_trades else "N/A"
                stats = load_stats()

                print(f"\n[{now}] #{self.cycle_count} {elapsed_min:.0f}m | Bal:${self.balance:.2f} Eq:${eq:.2f} ({pnl_pct:+.1f}%) | W:{self.wins} L:{self.losses} WR:{wr} | [{bar}] {progress:.0f}%")

                if self.positions:
                    for p in self.positions:
                        usage = self.get_margin_usage(p)
                        liq = self.calc_liquidation_price(p)
                        warn = " !!!" if usage >= LIQ_WARN_PCT else ""
                        warn = " !!" if usage >= LIQ_REDUCE_PCT else warn
                        warn = " !!!" if usage >= LIQ_EMERGENCY_PCT else warn
                        print(f"  {p['side']} {p['symbol']} @ ${p['entry']:.4f} TP:${p['tp']} SL:${p['sl']} PnL:${p['unrealized']:+.2f} Liq:${liq:.6f} Use:{usage*100:.0f}%{warn}")
                else:
                    print(f"  No positions | Reserve: ${self.balance:.2f}")

                if results:
                    top = sorted([r for r in results if r[2]["signal"] != "HOLD"], key=lambda x: x[2]["score"], reverse=True)[:5]
                    self.last_signals = []
                    for sym, price, sig, mtf in top:
                        m = sig.get("mtf", {})
                        self.last_signals.append({
                            "symbol": sym, "price": price, "signal": sig["signal"],
                            "score": sig["score"], "confirmations": sig["confirmations"],
                            "mtf_4h": m.get("4h", 0), "mtf_1h": m.get("1h", 0), "mtf_5m": m.get("5m", 0),
                        })
                    for sym, price, sig, mtf in top:
                        a = sig["analysis"]
                        m = sig.get("mtf", {})
                        print(f"  {sym}: ${price:.4f} | {sig['signal']}({sig['score']}/{sig.get('threshold',4)}c{sig['confirmations']}) 4H:{m.get('4h',0)} 1H:{m.get('1h',0)} 5M:{m.get('5m',0)} | RSI:{a.get('rsi',0):.0f} ST:{a.get('supertrend_dir','?')}")

                open_syms = {p["symbol"] for p in self.positions}
                cooldown_syms = set()
                for sym, (cycle, duration) in self.closed_symbols.items():
                    if self.cycle_count - cycle < duration: cooldown_syms.add(sym)
                can_open = len(self.positions) < MAX_POSITIONS and self.balance > 1.0 and not self.daily_paused

                if can_open:
                    signal_count = sum(1 for _, _, s, _ in results if s["signal"] in ("LONG", "SHORT"))
                    conf_count = sum(1 for _, _, s, _ in results if s["signal"] in ("LONG", "SHORT") and s.get("confirmations", 0) >= 4)
                    non_hold = sum(1 for _, _, s, _ in results if s["signal"] != "HOLD")
                    if self.cycle_count % 10 == 0 or conf_count > 0:
                        log.info(f"  Scan #{self.cycle_count}: {non_hold} signals, {conf_count} tradable, cooldowns={len(cooldown_syms)}")
                    opened_this_cycle = 0
                    for sym, price, sig, mtf in results:
                        if opened_this_cycle >= 1: break
                        if sig["signal"] in ("LONG", "SHORT") and sig.get("confirmations", 0) >= 4:
                            if sym in open_syms:
                                log.info(f"  SKIP {sym}: already open")
                                continue
                            if sym in cooldown_syms:
                                log.info(f"  SKIP {sym}: cooldown")
                                continue
                            ai = evaluate_signal(sig, sig.get("analysis", {}))
                            if not ai["approved"]:
                                log.info(f"  AI REJECTED {sym} {sig['signal']} conf_val={ai['confidence']:.2f} < {ai['min_confidence']:.2f}")
                                continue
                            log.info(f"  AI APPROVED {sym} {sig['signal']} conf_val={ai['confidence']:.2f}")
                            self.open_position(sym, sig["signal"], price, sig["analysis"])
                            opened_this_cycle += 1

                self.refresh_unrealized()
                eq = self.equity()

                try:
                    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
                        f.write(f"Equity: ${eq:.2f} | Bal: ${self.balance:.2f} | PnL: {pnl_pct:+.1f}% | W:{self.wins} L:{self.losses}")
                except Exception: pass
                save_state(self)
                for _ in range(4):
                    time.sleep(2)
                    self.refresh_unrealized()
                    save_state(self)

            except KeyboardInterrupt:
                print("\nStopped"); self.running = False
            except Exception as e:
                log.error(f"Error: {e}"); time.sleep(5)

        for i in reversed(range(len(self.positions))):
            k = self.get_klines(self.positions[i]["symbol"], "1m", 20)
            if k: self.close_position(i, float(k[-1]["close"]), "STOPPED")

        print(f"\n{'='*60}")
        print(f"  FINAL: ${self.start_balance:.2f} -> ${self.balance:.2f} | W:{self.wins} L:{self.losses} WR:{self.wins/self.total_trades*100:.0f}%" if self.total_trades else f"  FINAL: ${self.balance:.2f}")
        print(f"{'='*60}")


if __name__ == "__main__":
    SimBot().run()
