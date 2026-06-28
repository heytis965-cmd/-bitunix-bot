import requests
import logging

log = logging.getLogger("bitunix_bot")

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
TELEGRAM_ENABLED = False


def init_telegram(token, chat_id):
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
    TELEGRAM_BOT_TOKEN = token
    TELEGRAM_CHAT_ID = chat_id
    TELEGRAM_ENABLED = bool(token and chat_id)
    if TELEGRAM_ENABLED:
        send_message("Bot started")


def send_message(text, parse_mode="HTML"):
    if not TELEGRAM_ENABLED:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }, timeout=10)
        return resp.json().get("ok", False)
    except Exception as e:
        log.error(f"Telegram send error: {e}")
        return False


def notify_trade_open(symbol, side, entry, tp, sl, margin):
    emoji = "\u2b06\ufe0f" if side == "LONG" else "\u2b07\ufe0f"
    msg = (
        f"{emoji} <b>OPEN {side}</b> {symbol}\n"
        f"Entry: <code>${entry:.4f}</code>\n"
        f"TP: <code>${tp:.4f}</code> | SL: <code>${sl:.4f}</code>\n"
        f"Margin: <code>${margin:.2f}</code>"
    )
    send_message(msg)


def notify_trade_close(symbol, side, entry, exit_price, pnl, reason):
    if reason == "LIQUIDATED":
        emoji = "\U0001f4a5"
        msg = (
            f"{emoji} <b>LIQUIDATED {side}</b> {symbol}\n"
            f"Entry: <code>${entry:.4f}</code> -> <code>${exit_price:.4f}</code>\n"
            f"PnL: <code>${pnl:+.2f}</code> | LIQUIDATION"
        )
    else:
        emoji = "\u2705" if pnl > 0 else "\u274c"
        msg = (
            f"{emoji} <b>CLOSE {side}</b> {symbol}\n"
            f"Entry: <code>${entry:.4f}</code> -> <code>${exit_price:.4f}</code>\n"
            f"PnL: <code>${pnl:+.2f}</code> | {reason}"
        )
    send_message(msg)


def notify_status(balance, equity, pnl_pct, wins, losses, positions):
    pos_lines = []
    for p in positions:
        pos_lines.append(f"  {p['side']} {p['symbol']} PnL:${p.get('unrealized', 0):+.2f}")
    pos_text = "\n".join(pos_lines) if pos_lines else "  No positions"
    wr = f"{wins/(wins+losses)*100:.0f}%" if (wins + losses) > 0 else "N/A"
    msg = (
        f"\U0001f4ca <b>Status</b>\n"
        f"Bal: <code>${balance:.2f}</code> | Eq: <code>${equity:.2f}</code> ({pnl_pct:+.1f}%)\n"
        f"W:{wins} L:{losses} WR:{wr}\n"
        f"{pos_text}"
    )
    send_message(msg)


def notify_target_reached(balance, target):
    send_message(f"\U0001f389 <b>TARGET REACHED!</b> ${balance:.2f} (target ${target:.0f})")


def notify_game_over(balance):
    send_message(f"\U0001f4a8 <b>GAME OVER</b> Balance: ${balance:.2f}")


def notify_daily_loss_limit(loss):
    send_message(f"\u26a0\ufe0f <b>Daily loss limit</b> ${loss:.2f} - pausing trading")
