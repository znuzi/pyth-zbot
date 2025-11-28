import pandas as pd
from data_fetcher import fetch_historical_data
from bot.config import SYMBOLS, Z_ENTRY, Z_EXIT, POSITION_SIZE_USD, Z_ENTRY, Z_EXIT, POSITION_SIZE_USD

def run_backtest(symbol, data):
    df = data[symbol].copy()
    df['deviation'] = df['close'] - df['pyth_price']
    df['z_score'] = df['deviation'] / df['conf']
    
    position = 0
    trades = []
    balance = 10000
    
    for i in range(1, len(df)):
        z = df['z_score'].iloc[i]
        if position == 0:
            if z > Z_ENTRY:
                position = -1
                entry_price = df['close'].iloc[i]
            elif z < -Z_ENTRY:
                position = 1
                entry_price = df['close'].iloc[i]
        elif (position == 1 and z > -Z_EXIT) or (position == -1 and z < Z_EXIT):
            exit_price = df['close'].iloc[i]
            pnl = position * (exit_price - entry_price) / entry_price * POSITION_SIZE_USD
            balance += pnl
            trades.append(pnl)
            position = 0
    
    returns = pd.Series(trades).pct_change().dropna()
    sharpe = returns.mean() / returns.std() * (252**0.5) if len(returns) > 0 else 0
    max_dd = (pd.Series([balance] + [balance + sum(trades[:j+1]) for j in range(len(trades))]).cummax() - balance).min() / balance * 100
    monthly_ret = (balance / 10000 - 1) / (len(df)/ (24*30)) * 100
    win_rate = len([t for t in trades if t > 0]) / len(trades) * 100 if trades else 0
    
    return {
        'Monthly Return': f"+{monthly_ret:.1f}%",
        'Max DD': f"{max_dd:.1f}%",
        'Sharpe': f"{sharpe:.1f}",
        'Win Rate': f"{win_rate:.0f}%"
    }

if __name__ == "__main__":
    symbols = list(SYMBOLS.keys())
    data = fetch_historical_data(symbols, months=6)
    results = {}
    for sym in symbols:
        results[sym] = run_backtest(sym, data)
    
    df_results = pd.DataFrame(results).T
    print(df_results)
    # Outputs the table from README
