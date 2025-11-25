"""Backtest CVD validation logic on historical data"""
import asyncio
import sys
sys.path.insert(0, '..')

import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv
load_dotenv()

from core.exchange import ExchangeManager

async def backtest_cvd(symbol: str = "BTC/USDT:USDT", days: int = 7):
    """
    Backtest the CVD validation logic.
    Shows how many fake pumps would have been filtered.
    """
    print(f"🐆 CVD Backtest: {symbol}")
    print("=" * 60)
    
    exchange = ExchangeManager()
    await exchange.connect()
    
    try:
        # Fetch historical data (15m candles)
        candles_needed = days * 24 * 4  # 4 candles per hour
        ohlcv = await exchange.fetch_ohlcv(symbol, '15m', limit=min(candles_needed, 1000))
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate SuperTrend
        supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3.0)
        df['supertrend'] = supertrend['SUPERT_10_3.0']
        df['st_direction'] = supertrend['SUPERTd_10_3.0']
        
        # Calculate CVD
        df['buy_vol'] = df.apply(lambda x: x['volume'] if x['close'] > x['open'] else 0, axis=1)
        df['sell_vol'] = df.apply(lambda x: x['volume'] if x['close'] < x['open'] else 0, axis=1)
        df['cvd'] = (df['buy_vol'] - df['sell_vol']).cumsum()
        
        # Simulate OI surge (using volume as proxy since we don't have historical OI)
        df['vol_ma'] = df['volume'].rolling(4).mean()
        df['vol_surge'] = df['volume'] > (df['vol_ma'] * 1.5)
        
        # Find potential signals
        df['price_up'] = df['close'] > df['close'].shift(1)
        df['cvd_up'] = df['cvd'] > df['cvd'].shift(1)
        df['uptrend'] = df['close'] > df['supertrend']
        
        # Count signals
        potential_longs = df[(df['uptrend']) & (df['vol_surge'])].copy()
        
        valid_signals = potential_longs[potential_longs['cvd_up']]
        fake_pumps = potential_longs[~potential_longs['cvd_up']]
        
        print(f"\nData period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        print(f"Total candles: {len(df)}")
        print(f"\n📊 Signal Analysis:")
        print(f"   Potential long signals: {len(potential_longs)}")
        print(f"   ✅ Valid (CVD confirmed): {len(valid_signals)}")
        print(f"   🚫 Rejected (fake pumps): {len(fake_pumps)}")
        print(f"   Filter rate: {len(fake_pumps)/len(potential_longs)*100:.1f}%" if len(potential_longs) > 0 else "   No signals")
        
        # Show some examples
        if len(fake_pumps) > 0:
            print(f"\n🚫 Example Fake Pumps Filtered:")
            for _, row in fake_pumps.head(3).iterrows():
                print(f"   {row['timestamp']}: Price UP but CVD DOWN")
        
        if len(valid_signals) > 0:
            print(f"\n✅ Example Valid Signals:")
            for _, row in valid_signals.head(3).iterrows():
                print(f"   {row['timestamp']}: Price UP + CVD UP (confirmed)")
        
    finally:
        await exchange.close()

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC/USDT:USDT"
    asyncio.run(backtest_cvd(symbol))
