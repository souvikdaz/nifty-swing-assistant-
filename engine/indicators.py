import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes key technical indicators for swing trading on daily OHLCV data.
    Ensures safe handling of column names whether single-level or multi-index.
    """
    if df is None or len(df) < 20:
        return df

    # Flatten multi-index columns if present (common in recent yfinance)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.copy()

    # Standardize column names
    col_map = {c: c.capitalize() for c in df.columns}
    df.rename(columns=col_map, inplace=True)

    # 1. Exponential Moving Averages (Trend Filters)
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    if len(df) >= 200:
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    else:
        df['EMA_200'] = np.nan

    # 2. RSI (14) - Momentum
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)

    # 3. MACD (12, 26, 9)
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # 4. Average True Range (ATR 14) for Risk Management & Volatility
    high_low = df['High'] - df['Low']
    high_close_prev = (df['High'] - df['Close'].shift()).abs()
    low_close_prev = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100

    # 5. Volume Indicators
    df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA_20'].replace(0, np.nan)

    # 6. Bollinger Bands (20, 2)
    sma_20 = df['Close'].rolling(window=20).mean()
    std_20 = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = sma_20 + (2 * std_20)
    df['BB_Lower'] = sma_20 - (2 * std_20)
    df['BB_Middle'] = sma_20

    # 7. SuperTrend (10, 3)
    period = 10
    multiplier = 3
    hl2 = (df['High'] + df['Low']) / 2
    atr_st = tr.rolling(window=period).mean().bfill().fillna(0)

    basic_upper = hl2 + (multiplier * atr_st)
    basic_lower = hl2 - (multiplier * atr_st)

    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    supertrend = pd.Series(index=df.index, dtype='float64')
    st_direction = pd.Series(1, index=df.index, dtype='int32')

    for i in range(1, len(df)):
        # Final Upper
        if basic_upper.iloc[i] < final_upper.iloc[i-1] or df['Close'].iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]

        # Final Lower
        if basic_lower.iloc[i] > final_lower.iloc[i-1] or df['Close'].iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]

        # Trend direction
        if df['Close'].iloc[i] > final_upper.iloc[i-1]:
            st_direction.iloc[i] = 1
        elif df['Close'].iloc[i] < final_lower.iloc[i-1]:
            st_direction.iloc[i] = -1
        else:
            st_direction.iloc[i] = st_direction.iloc[i-1]

        supertrend.iloc[i] = final_lower.iloc[i] if st_direction.iloc[i] == 1 else final_upper.iloc[i]

    df['SuperTrend'] = supertrend.bfill().fillna(df['Close'])
    df['SuperTrend_Direction'] = st_direction.fillna(1).astype(int)

    # 8. Support / Resistance (20-day High / Low)
    df['Resist_20'] = df['High'].rolling(window=20).max()
    df['Support_20'] = df['Low'].rolling(window=20).min()

    # 9. Bullish Reversal Candlestick Signals
    # Hammer / Pin Bar
    body = (df['Close'] - df['Open']).abs()
    lower_wick = np.minimum(df['Open'], df['Close']) - df['Low']
    upper_wick = df['High'] - np.maximum(df['Open'], df['Close'])
    candle_range = df['High'] - df['Low']
    
    is_hammer = (lower_wick >= 2 * body) & (upper_wick <= 0.2 * candle_range) & (candle_range > 0)
    is_bullish_engulfing = (
        (df['Close'] > df['Open']) & 
        (df['Close'].shift(1) < df['Open'].shift(1)) & 
        (df['Close'] >= df['Open'].shift(1)) & 
        (df['Open'] <= df['Close'].shift(1))
    )
    df['Bullish_Hammer'] = is_hammer
    df['Bullish_Engulfing'] = is_bullish_engulfing

    return df
