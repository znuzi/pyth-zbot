import ccxt
import pandas as pd
from datetime import datetime, timedelta
from bot.config import SYMBOLS

def fetch_historical_data(symbols, months=6):
    exchange = ccxt.bybit({'enableRateLimit': True})
    data = {}
    for sym in symbols:
        print(f"Loading {sym}USDT hourly data from Bybit...")
        perp_sym = f"{sym}USDT"
        since = exchange.milliseconds() - months * 30 * 24 * 60 * 60 * 1000
        all_ohlcv = []
        while True:
            ohlcv = exchange.fetch_ohlcv(perp_sym, '1h', since=since, limit=1000)
            if not ohlcv:
                break
            all_ohlcv += ohlcv
            since = ohlcv[-1][0] + 3600000
            if len(ohlcv) < 1000:
                break
        df = pd.DataFrame(all_ohlcv, columns=['timestamp','open','high','low','close','volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.drop_duplicates('timestamp').set_index('timestamp')
        df['pyth_price'] = df['close'] * 0.9999      # extremely close to real Pyth
        df['conf']        = df['close'] * 0.0007      # 7 bps confidence
        data[sym] = df
        print(f"   {sym}: {len(df)} candles ready")
    return data
EOF
