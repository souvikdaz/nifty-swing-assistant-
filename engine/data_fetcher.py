import os
import json
import time
import pandas as pd
import numpy as np
import yfinance as yf
from engine.indicators import calculate_indicators

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_FILE = os.path.join(DATA_DIR, "cache_history.pkl")

# In-memory cache
_CACHE = {}
_CACHE_TIME = {}
CACHE_EXPIRY_SEC = 300  # 5 minutes cache

def load_stock_universe():
    stocks_path = os.path.join(DATA_DIR, "nifty_stocks.json")
    with open(stocks_path, "r") as f:
        return json.load(f)

def clean_yf_df(df: pd.DataFrame, ticker: str = None) -> pd.DataFrame:
    """Safely unpacks yfinance dataframe handling MultiIndex columns."""
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        # Check if ticker level exists
        if ticker and ticker in df.columns.levels[1]:
            df = df.xs(ticker, axis=1, level=1)
        else:
            # Flatten to first level
            df.columns = [col[0] for col in df.columns]

    df = df.dropna(how="all")
    return df

def fetch_ticker_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetches history for a single ticker with caching."""
    cache_key = f"{symbol}_{period}_{interval}"
    now = time.time()
    
    if cache_key in _CACHE and (now - _CACHE_TIME.get(cache_key, 0)) < CACHE_EXPIRY_SEC:
        return _CACHE[cache_key].copy()

    try:
        t = yf.Ticker(symbol)
        df = t.history(period=period, interval=interval)
        if df.empty:
            # Fallback to download
            df = yf.download(symbol, period=period, interval=interval, progress=False)

        df = clean_yf_df(df, symbol)
        if not df.empty:
            df = calculate_indicators(df)
            _CACHE[cache_key] = df
            _CACHE_TIME[cache_key] = now
            return df.copy()
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

    return pd.DataFrame()

def fetch_batch_stocks(symbols: list, period: str = "1y") -> dict:
    """
    Fetches data for multiple stocks efficiently.
    Returns dict of symbol -> pd.DataFrame (with indicators).
    """
    results = {}
    missing = []
    now = time.time()

    for s in symbols:
        cache_key = f"{s}_{period}_1d"
        if cache_key in _CACHE and (now - _CACHE_TIME.get(cache_key, 0)) < CACHE_EXPIRY_SEC:
            results[s] = _CACHE[cache_key].copy()
        else:
            missing.append(s)

    if missing:
        # Download in batch for speed
        try:
            batch_df = yf.download(missing, period=period, interval="1d", group_by="ticker", progress=False)
            for s in missing:
                try:
                    if len(missing) == 1:
                        sub_df = clean_yf_df(batch_df)
                    else:
                        if s in batch_df.columns.levels[0]:
                            sub_df = batch_df[s].copy()
                        else:
                            sub_df = pd.DataFrame()

                    sub_df = sub_df.dropna(how="all")
                    if not sub_df.empty and len(sub_df) >= 20:
                        sub_df = calculate_indicators(sub_df)
                        cache_key = f"{s}_{period}_1d"
                        _CACHE[cache_key] = sub_df
                        _CACHE_TIME[cache_key] = now
                        results[s] = sub_df
                except Exception as ex:
                    print(f"Error parsing batch for {s}: {ex}")
        except Exception as e:
            print(f"Batch fetch failed: {e}. Falling back to single ticker fetch.")
            for s in missing:
                df = fetch_ticker_data(s, period=period)
                if not df.empty:
                    results[s] = df

    return results

def get_nifty_regime() -> dict:
    """
    Determines market regime for NIFTY 50 index (^NSEI).
    Essential for swing trading: 'Trade with the trend'.
    """
    df = fetch_ticker_data("^NSEI", period="1y")
    if df.empty or len(df) < 50:
        return {
            "status": "Unknown",
            "close": 0.0,
            "change_pct": 0.0,
            "rsi": 50.0,
            "trend": "Neutral",
            "message": "NIFTY data currently unavailable."
        }

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    close = float(last_row['Close'])
    prev_close = float(prev_row['Close'])
    change_pct = ((close - prev_close) / prev_close) * 100

    ema_20 = float(last_row.get('EMA_20', close))
    ema_50 = float(last_row.get('EMA_50', close))
    ema_200 = float(last_row.get('EMA_200', close))
    rsi = float(last_row.get('RSI', 50.0))
    st_val = last_row.get('SuperTrend_Direction', 1)
    st_dir = 1 if (pd.isna(st_val) or not isinstance(st_val, (int, float, np.number))) else int(st_val)

    # Determine trend regime
    if close > ema_20 and ema_20 > ema_50 and st_dir == 1:
        if close > ema_200:
            regime = "Strong Bullish"
            stance = "Aggressive Swing Longs Allowed (High Probability)"
        else:
            regime = "Bullish Pullback in Bearish Structure"
            stance = "Selective Swing Longs with Tight Stops"
    elif close < ema_20 and close < ema_50 and st_dir == -1:
        if close < ema_200:
            regime = "Strong Bearish"
            stance = "Extreme Caution: Avoid buying swings or trade defensively"
        else:
            regime = "Correction in Primary Uptrend"
            stance = "Wait for reversal candles near key support"
    else:
        regime = "Consolidating / Choppy"
        stance = "Neutral: Be selective, stick to top strength leaders"

    return {
        "status": regime,
        "stance": stance,
        "close": round(close, 2),
        "prev_close": round(prev_close, 2),
        "change_pct": round(change_pct, 2),
        "rsi": round(rsi, 1),
        "ema_20": round(ema_20, 2),
        "ema_50": round(ema_50, 2),
        "ema_200": round(ema_200, 2) if not np.isnan(ema_200) else "N/A",
        "supertrend_direction": "Bullish" if st_dir == 1 else "Bearish"
    }
