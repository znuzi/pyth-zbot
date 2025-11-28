cat > backtest/data_fetcher.py << 'EOF'
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from bot.config import SYMBOLS

def fetch_historical_data(symbols, months=6):
    exchange = ccxt.bybit({'enableRateLimit': True})
    data = {}
    
    for sym in symbols:
        print(f"Fetching {sym}USDT perpetual data from Bybit...")
        perp_sym = f"{sym}USDT"
        since = int((datetime.now() - timedelta(days=months*35)).timestamp() * 1000)
        all_ohlcv = []
        while True:
            ohlcv = exchange.fetch_ohlcv(perp_sym, timeframe='1h', since=since, limit=1000)
            if len(ohlcv) == 0:
                break
            all_ohlcv += ohlcv
            since = ohlcv[-1][0] + 3600000  # move forward 1 hour
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.drop_duplicates(subset=['timestamp']).set_index('timestamp')
        
        # Simulate Pyth price (extremely close in practice for perps)
        df['pyth_price'] = df['close'] * 0.9999
        df['conf'] = df['close'] * 0.0007   # ≈7 bps confidence
        
        data[sym] = df
        print(f"   {sym}: {len(df)} hourly candles loaded")
    
    return data
EOF
