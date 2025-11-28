cat > backtest/data_fetcher.py << 'EOF'
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from bot.config import SYMBOLS

def fetch_historical_data(symbols, months=6):
    exchange = ccxt.bybit({'enableRateLimit': True})
    data = {}
    
    for sym in symbols:
        print(f"Fetching {sym} perpetual data from Bybit...")
        perp_sym = f"{sym}USDT"
        since = int((datetime.now() - timedelta(days=months*31)).timestamp() * 1000)
        ohlcv = exchange.fetch_ohlcv(perp_sym, timeframe='1h', since=since, limit=2000)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Use close price as Pyth "fair price" for backtest (very close in practice)
        df['pyth_price'] = df['close'] * 0.9998
        df['conf'] = df['close'] * 0.0008  # ~8 bps confidence
        
        data[sym] = df.set_index('timestamp')
        print(f"   {sym}: {len(df)} hourly candles loaded")
    
    return data
EOF
