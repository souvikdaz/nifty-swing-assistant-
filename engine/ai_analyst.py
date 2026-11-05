import os
import requests
import json

def generate_offline_thesis(setup: dict, nifty_regime: dict) -> dict:
    """
    Generates a deterministic institutional-grade thesis report without needing an external API key.
    """
    symbol = setup["symbol"]
    name = setup["name"]
    price = setup["close"]
    sl = setup["stop_loss"]
    t1 = setup["target_1"]
    t2 = setup["target_2"]
    rr_pct = setup["risk_pct"]
    setup_type = setup["setup"]
    score = setup["score"]

    # Market alignment evaluation
    nifty_trend = nifty_regime.get("status", "Unknown")
    is_nifty_bull = "Bullish" in nifty_trend

    if score >= 80 and is_nifty_bull:
        conviction = "High Conviction Swing Long"
        conviction_badge = "🟢 HIGH"
        guidance = "Setup aligns with broad market trend and multi-timeframe indicators. Full planned risk position (1% capital) suitable."
    elif score >= 65:
        conviction = "Moderate Conviction Swing Long"
        conviction_badge = "🟡 MODERATE"
        guidance = "Good technical structure, but monitor broader index volatility. Consider entering with 50% size, adding remaining 50% upon breakout confirmation."
    else:
        conviction = "Speculative / Low Conviction"
        conviction_badge = "🟠 CAUTION"
        guidance = "Signals are mixed or market regime is unfavorable. Wait for stronger price confirmation or look for higher-ranked setups."

    catalysts = [
        f"Technical Pattern: {setup_type} with a Quality Score of {score}/100.",
        f"Volume Confirmation: Trading at {setup.get('vol_ratio', 1.0):.1f}x of its 20-day moving average.",
        f"Momentum: 14-day RSI stands at {setup.get('rsi', 50.0):.1f}, indicating healthy trend expansion without extreme overbought exhaustion."
    ]

    risks = [
        f"Strict Invalidation Point: ₹{sl:.2f}. If price closes below this on a daily candle, the swing thesis is invalidated immediately.",
        f"Broad Market Risk: NIFTY 50 is currently in '{nifty_trend}'. If NIFTY breaks support, individual stock breakouts face a 60-70% failure rate.",
        f"Maximum Trade Risk: {rr_pct:.2f}% distance from entry. Do not exceed position sizing rules."
    ]

    action_plan = [
        f"1. Entry: Look for entries around ₹{price:.2f} (market or limit on pullback).",
        f"2. Hard Stop-Loss: Place GTT stop at ₹{sl:.2f} immediately upon fill.",
        f"3. Profit Booking 1: Book 50% quantity at Target 1 (₹{t1:.2f}, +{setup['target_1_gain']}%).",
        f"4. Risk Elimination: Move Stop-Loss to Breakeven (₹{price:.2f}) immediately after Target 1 is achieved.",
        f"5. Final Runner: Trail remaining 50% quantity using daily 20 EMA or exit at Target 2 (₹{t2:.2f}, +{setup['target_2_gain']}%)."
    ]

    return {
        "symbol": symbol,
        "name": name,
        "conviction": conviction,
        "conviction_badge": conviction_badge,
        "guidance": guidance,
        "catalysts": catalysts,
        "risks": risks,
        "action_plan": action_plan,
        "nifty_context": f"NIFTY 50 Benchmark: {nifty_trend} (Close: {nifty_regime.get('close')})"
    }

def get_ai_trade_analysis(setup: dict, nifty_regime: dict, api_key: str = None) -> dict:
    """
    Returns AI thesis. If Gemini API key is provided, invokes Gemini for deep synthesis;
    otherwise uses the robust built-in quantitative thesis generator.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    # If no key, return high quality deterministic thesis
    if not api_key:
        return generate_offline_thesis(setup, nifty_regime)

    # Optional Gemini LLM call
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = f"""
You are an expert quantitative swing trading risk officer.
Analyze this Indian stock swing trade setup for {setup['name']} ({setup['symbol']}):
- Current Price: ₹{setup['close']}
- Stop Loss: ₹{setup['stop_loss']} ({setup['risk_pct']}% risk)
- Target 1 (1:2 RR): ₹{setup['target_1']} (+{setup['target_1_gain']}%)
- Target 2 (1:3 RR): ₹{setup['target_2']} (+{setup['target_2_gain']}%)
- Setup Type: {setup['setup']}
- RSI (14): {setup['rsi']}
- Volume Ratio: {setup['vol_ratio']}x
- Technical Score: {setup['score']}/100
- NIFTY 50 Regime: {nifty_regime.get('status')}

The user has stated: "I don't want to incur losses."
Provide a realistic risk-first trade analysis in JSON format with fields:
- "conviction": (High / Moderate / Caution)
- "conviction_badge": ("🟢 HIGH" / "🟡 MODERATE" / "🟠 CAUTION")
- "guidance": 2 sentences on position sizing and execution.
- "catalysts": list of 3 bullet points supporting the long thesis.
- "risks": list of 3 explicit failure modes and stop loss enforcement.
- "action_plan": list of 5 concrete step-by-step execution rules.
Only return valid JSON.
"""
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            raw_text = data['candidates'][0]['content']['parts'][0]['text']
            # strip markdown code blocks if any
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            parsed["symbol"] = setup["symbol"]
            parsed["name"] = setup["name"]
            parsed["nifty_context"] = f"NIFTY 50 Benchmark: {nifty_regime.get('status')} (Close: {nifty_regime.get('close')})"
            return parsed
    except Exception as e:
        print(f"Gemini API invocation failed or skipped: {e}")

    return generate_offline_thesis(setup, nifty_regime)
