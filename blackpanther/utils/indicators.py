"""
Custom technical indicators that don't require numba
Works with Python 3.14+
"""
import pandas as pd
import numpy as np


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, 
               length: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Calculate SuperTrend indicator without numba dependency.
    
    Args:
        high: High prices
        low: Low prices  
        close: Close prices
        length: ATR period (default 10)
        multiplier: ATR multiplier (default 3.0)
    
    Returns:
        DataFrame with 'supertrend' and 'direction' columns
    """
    # Calculate ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=length).mean()
    
    # Calculate basic upper and lower bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize SuperTrend
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    # First valid value
    first_valid = length
    supertrend.iloc[first_valid] = upper_band.iloc[first_valid]
    direction.iloc[first_valid] = -1
    
    # Calculate SuperTrend
    for i in range(first_valid + 1, len(close)):
        # Previous values
        prev_supertrend = supertrend.iloc[i-1]
        prev_upper = upper_band.iloc[i-1]
        prev_lower = lower_band.iloc[i-1]
        prev_close = close.iloc[i-1]
        
        # Current values
        curr_upper = upper_band.iloc[i]
        curr_lower = lower_band.iloc[i]
        curr_close = close.iloc[i]
        
        # Adjust bands
        if curr_lower > prev_lower or prev_close < prev_lower:
            final_lower = curr_lower
        else:
            final_lower = prev_lower
            
        if curr_upper < prev_upper or prev_close > prev_upper:
            final_upper = curr_upper
        else:
            final_upper = prev_upper
        
        # Determine trend
        if prev_supertrend == prev_upper:
            if curr_close > final_upper:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1
        else:
            if curr_close < final_lower:
                supertrend.iloc[i] = final_upper
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = final_lower
                direction.iloc[i] = 1
    
    return pd.DataFrame({
        f'SUPERT_{length}_{multiplier}': supertrend,
        f'SUPERTd_{length}_{multiplier}': direction
    })


def calculate_cvd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cumulative Volume Delta (CVD).
    
    Logic: Estimate Buy vs Sell Volume
    - If Close > Open, assume Aggressive Buyers
    - If Close < Open, assume Aggressive Sellers
    """
    df = df.copy()
    df['buy_vol'] = df.apply(
        lambda x: x['volume'] if x['close'] > x['open'] else 0, 
        axis=1
    )
    df['sell_vol'] = df.apply(
        lambda x: x['volume'] if x['close'] < x['open'] else 0, 
        axis=1
    )
    df['cvd'] = (df['buy_vol'] - df['sell_vol']).cumsum()
    return df


def calculate_rvol(current_volume: float, avg_volume: float) -> float:
    """
    Calculate Relative Volume (RVOL).
    
    Args:
        current_volume: Today's volume
        avg_volume: Average volume (e.g., 10-day average)
    
    Returns:
        RVOL multiplier (e.g., 5.0 = 500% of average)
    """
    if avg_volume <= 0:
        return 0.0
    return current_volume / avg_volume


def calculate_basis(perp_price: float, spot_price: float) -> float:
    """
    Calculate basis spread between perpetual and spot.
    
    Args:
        perp_price: Perpetual contract price
        spot_price: Spot market price
    
    Returns:
        Basis as decimal (e.g., 0.01 = 1%)
    """
    if spot_price <= 0:
        return 0.0
    return (perp_price - spot_price) / spot_price
