import ccxt
import requests
import pandas as pd
from datetime import datetime, timedelta
from config import SYMBOLS

def fetch_historical_data(symbols, months=6):
    exchange = ccxt.bybit({'enableRateLimit': True})
    exchange.set_sandbox_mode(True)  # Historical is same
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months*30)
    
    data = {}
    for sym in symbols:
        perp_sym = f"{sym}USDT"
        ohlcv = exchange.fetch_ohlcv(perp_sym, timeframe='1h', since=int(start_date.timestamp()*1000), limit=months*24*30)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        data[sym] = df
        
        # Pyth historical (mock endpoint - use real /v1/historical)
        pyth_url = f"https://hermes.pyth.network/v1/historical_price_feeds?ids[]={SYMBOLS[sym]['pyth_id']}&start_time={int(start_date.timestamp())}&end_time={int(end_date.timestamp())}"
        pyth_resp = requests.get(pyth_url).json()
        # Parse pyth_resp into df['pyth_price'] and df['conf'] (simplified)
        df['pyth_price'] = df['close'] * 0.999  # Mock for demo; replace with real parse
        df['conf'] = df['close'] * 0.001
        data[sym] = df
    return data
