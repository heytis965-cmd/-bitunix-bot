import sys, traceback
sys.path.insert(0, r"C:\Users\Леонид\Mimo_Projects\bitunix_bot")
from simulator import SimBot, save_state

try:
    bot = SimBot()
    print("Bot init OK")
    bot.check_smart_exit()
    print("check_smart_exit OK")
    bot.check_liquidation_protection()
    print("check_liquidation_protection OK")
    dd = bot.check_max_drawdown()
    print(f"check_max_drawdown OK: {dd}")
    print(f"Balance: {bot.balance}")
    print(f"Positions: {len(bot.positions)}")
    for p in bot.positions:
        usage = bot.get_margin_usage(p)
        liq = bot.calc_liquidation_price(p)
        sym = p["symbol"]
        side = p["side"]
        print(f"  {side} {sym} usage={usage*100:.1f}% liq={liq:.6f}")
    save_state(bot)
    print("State saved OK")
except Exception as e:
    traceback.print_exc()
