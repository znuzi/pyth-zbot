#!/usr/bin/env python3
import time
import os
from dotenv import load_dotenv
import ccxt
from datetime import datetime
from pythclient import PythHttpClient  # pip install pythclient
from config import SYMBOLS, Z_ENTRY, Z_EXIT, POSITION_SIZE_USD, POLL_INTERVAL
from alerts import send_telegram_alert
import asyncio

load_dotenv()

# Bybit exchange setup
exchange = ccxt.bybit({
    'apiKey': os.getenv('BYBIT_API_KEY'),
    'secret': os.getenv('BYBIT_API_SECRET'),
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(os.getenv('BYBIT_TESTNET', 'true').lower() == 'true')

client = PythHttpClient(endpoint='https://hermes.pyth.network')  # Free Pyth tier
print(f"[{datetime.now()}] Pyth Z-Bot started | Symbols: {list(SYMBOLS.keys())} | Testnet: {exchange.sandbox_mode}")

positions = {sym: 0 for sym in SYMBOLS}  # 1=long, -1=short, 0=flat
initial_balance = float(os.getenv('INITIAL_BALANCE', 10000))  # Mock for testnet

async def main_loop():
    while True:
        try:
            current_balance = exchange.fetch_balance()['USDT']['free'] if not exchange.sandbox_mode else initial_balance
            pnl = current_balance - initial_balance
            pnl_pct = (pnl / initial_balance) * 100

            # Alert on PnL thresholds
            if abs(pnl_pct) >= 5:
                await send_telegram_alert(f"💰 PnL Update: ${pnl:+.2f} ({pnl_pct:+.1f}%)")

            for symbol in SYMBOLS:
                perp_sym = f"{symbol}USDT"
                pyth_id = SYMBOLS[symbol]['pyth_id']

                # Fetch Pyth price
                price_update = client.get_latest_price_update(pyth_id)
                pyth_price = price_update.price
                conf = price_update.conf

                # Fetch Bybit perp price
                ticker = exchange.fetch_ticker(perp_sym)
                perp_price = ticker['last']

                # Calculate z-score
                deviation = perp_price - pyth_price
                z_score = deviation / conf if conf > 0 else 0

                print(f"{symbol}: Pyth {pyth_price:.1f} ±{conf:.1f} | Perp {perp_price:.1f} | Z {z_score:+.2f} | Pos {positions[symbol]}")

                # Trading logic
                pos = positions[symbol]
                size = POSITION_SIZE_USD / perp_price
                if pos == 0:  # Enter
                    if z_score > Z_ENTRY:
                        exchange.create_market_sell_order(perp_sym, size)
                        positions[symbol] = -1
                        await send_telegram_alert(f"🔴 SHORT {symbol} @ ${perp_price:.1f} | Z: {z_score:+.2f}")
                    elif z_score < -Z_ENTRY:
                        exchange.create_market_buy_order(perp_sym, size)
                        positions[symbol] = 1
                        await send_telegram_alert(f"🟢 LONG {symbol} @ ${perp_price:.1f} | Z: {z_score:+.2f}")
                else:  # Exit
                    exit_condition = (pos == 1 and z_score > -Z_EXIT) or (pos == -1 and z_score < Z_EXIT)
                    if exit_condition:
                        if pos == 1:
                            exchange.create_market_sell_order(perp_sym, size)
                        else:
                            exchange.create_market_buy_order(perp_sym, size)
                        await send_telegram_alert(f"✅ Closed {symbol} | Z: {z_score:+.2f}")
                        positions[symbol] = 0

            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"Error: {e}")
            await send_telegram_alert(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_loop())
