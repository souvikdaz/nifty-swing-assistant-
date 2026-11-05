import pandas as pd
import numpy as np

def analyze_swing_setup(df: pd.DataFrame, symbol: str, stock_name: str, sector: str) -> dict:
    """
    Evaluates whether a stock meets high-probability swing criteria.
    Enforces strict risk management parameters (Stop Loss and Target).
    """
    if df is None or len(df) < 50:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = float(last['Close'])
    open_p = float(last['Open'])
    high = float(last['High'])
    low = float(last['Low'])
    prev_close = float(prev['Close'])

    ema_20 = float(last.get('EMA_20', close))
    ema_50 = float(last.get('EMA_50', close))
    ema_200 = float(last.get('EMA_200', np.nan))
    rsi = float(last.get('RSI', 50.0))
    atr = float(last.get('ATR', close * 0.02))
    vol_ratio = float(last.get('Vol_Ratio', 1.0))
    st_val = last.get('SuperTrend_Direction', 1)
    st_dir = 1 if (pd.isna(st_val) or not isinstance(st_val, (int, float, np.number))) else int(st_val)

    resist_20 = float(prev.get('Resist_20', high))
    support_20 = float(prev.get('Support_20', low))

    score = 0
    signals = []
    setup_name = None

    # Trend baseline
    is_above_200 = not np.isnan(ema_200) and close > ema_200
    if is_above_200:
        score += 20
        signals.append("Trading above 200 EMA (Long-term Bullish)")

    is_golden_trend = ema_20 > ema_50
    if is_golden_trend:
        score += 15
        signals.append("EMA 20 > EMA 50 (Short-term momentum aligned)")

    # Volume confirmation
    if vol_ratio >= 1.4:
        score += 15
        signals.append(f"Volume Surge: {vol_ratio:.1f}x 20-day average")
    elif vol_ratio >= 1.0:
        score += 5

    # Candlestick strength
    is_green = close > open_p
    is_hammer = bool(last.get('Bullish_Hammer', False))
    is_engulf = bool(last.get('Bullish_Engulfing', False))

    if is_engulf:
        score += 15
        signals.append("Bullish Engulfing Candlestick pattern")
    elif is_hammer:
        score += 15
        signals.append("Hammer / Rejection Wick pattern")
    elif is_green and close > prev_close:
        score += 5

    # Setup Identification
    # SETUP A: EMA Pullback (Best for risk management)
    near_ema20 = abs(close - ema_20) / close <= 0.015
    near_ema50 = abs(close - ema_50) / close <= 0.02
    if is_above_200 and (near_ema20 or near_ema50) and (is_green or is_hammer) and rsi < 65:
        setup_name = "EMA Pullback Reversal"
        score += 25
        signals.append("Bouncing off key EMA support in uptrend")
        stop_loss = round(min(low, ema_50 - (0.5 * atr)), 2)

    # SETUP B: Breakout with Volume
    elif close >= resist_20 and vol_ratio >= 1.3 and 55 <= rsi <= 72:
        setup_name = "High-Volume Range Breakout"
        score += 25
        signals.append("Fresh 20-day high breakout with heavy volume")
        stop_loss = round(max(prev['Low'], close - (1.5 * atr)), 2)

    # SETUP C: Oversold Rebound in Quality Stock
    elif is_above_200 and rsi <= 40 and is_green and (close > prev_close):
        setup_name = "Oversold Trend Bounce"
        score += 20
        signals.append(f"Oversold RSI ({rsi:.1f}) reversing in major bull trend")
        stop_loss = round(low - (0.8 * atr), 2)

    # Fallback default setup
    else:
        if is_above_200 and is_golden_trend and st_dir == 1 and 45 <= rsi <= 65:
            setup_name = "Trend Continuation"
            score += 15
            stop_loss = round(close - (1.8 * atr), 2)
        else:
            return None  # No valid safe swing setup

    # Calculate Risk & Targets
    risk_per_share = close - stop_loss
    if risk_per_share <= 0:
        stop_loss = round(close - (1.5 * atr), 2)
        risk_per_share = close - stop_loss

    risk_pct = (risk_per_share / close) * 100

    # Risk gate: We reject setups where stop loss is too wide (> 6%) or too tight (< 0.8%)
    if risk_pct > 6.5 or risk_pct < 0.7:
        return None

    target_1 = round(close + (2.0 * risk_per_share), 2)  # 1:2 RR
    target_2 = round(close + (3.0 * risk_per_share), 2)  # 1:3 RR

    target_1_gain = round(((target_1 - close) / close) * 100, 2)
    target_2_gain = round(((target_2 - close) / close) * 100, 2)

    return {
        "symbol": symbol,
        "name": stock_name,
        "sector": sector,
        "setup": setup_name,
        "score": min(score, 100),
        "close": round(close, 2),
        "change_pct": round(((close - prev_close) / prev_close) * 100, 2),
        "rsi": round(rsi, 1),
        "atr": round(atr, 2),
        "vol_ratio": round(vol_ratio, 2),
        "stop_loss": stop_loss,
        "risk_per_share": round(risk_per_share, 2),
        "risk_pct": round(risk_pct, 2),
        "target_1": target_1,
        "target_1_gain": target_1_gain,
        "target_2": target_2,
        "target_2_gain": target_2_gain,
        "risk_reward": "1 : 2.0 (Target 1) / 1 : 3.0 (Target 2)",
        "signals": signals
    }

def screen_nifty_universe(stocks_data_dict: dict, universe_meta: list) -> list:
    """
    Screens all constituent stocks and returns qualified swing setups
    ranked by Quality Score descending.
    """
    meta_lookup = {item["symbol"]: item for item in universe_meta}
    opportunities = []

    for sym, df in stocks_data_dict.items():
        if df is None or df.empty:
            continue
        meta = meta_lookup.get(sym, {"name": sym, "sector": "General"})
        setup = analyze_swing_setup(df, sym, meta["name"], meta["sector"])
        if setup:
            opportunities.append(setup)

    # Sort primarily by Quality Score, then by favorable risk percentage
    opportunities.sort(key=lambda x: (x["score"], -x["risk_pct"]), reverse=True)
    return opportunities
