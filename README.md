# 🛡️ NIFTY Swing AI Assistant

An intelligent, capital-preservation swing trading assistant for the Indian stock market (NIFTY 50 and key liquid stocks).

---

## 🎯 The Philosophy: How to Avoid Trading Losses

The golden rule of institutional trading is: **"You cannot control the market; you can only control your risk."**

No algorithm or human trader wins 100% of trades. Traders who try to avoid taking small losses inevitably hold losers until they turn into devastating losses. 

This AI Assistant is architected to protect your capital using three mathematical pillars:
1. **Never risk more than 1% of total capital on a single trade**: Using fixed-fractional position sizing.
2. **Strict Minimum 1:2 Risk-Reward Ratio**: A 50% win rate produces solid net profit because winners are 2x to 3x larger than losers.
3. **Breakeven Rule**: As soon as Target 1 is reached (+2x the risk), the stop loss is automatically moved to entry cost, turning the trade completely risk-free.
4. **Zero Forced Trades**: When the market is unfavorable or no setups meet criteria, the safest position is 100% Cash.

---

## 🚀 Quick Start

### 1. Launch Dashboard
Run the start script from the project folder:
```bash
cd /Users/sdazz/nifty-swing-assistant
./run.sh
```

Or using the virtual environment directly:
```bash
cd /Users/sdazz/nifty-swing-assistant
./venv/bin/streamlit run app.py
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 📦 Features & Dashboard Tabs

### 1. 🎯 Swing Screener & Trade Ideas
- Scans NIFTY 50 stocks for 3 quantitative swing patterns:
  - **EMA Pullback Reversal**: Trend-following pullback to the 20 or 50 EMA.
  - **High-Volume Range Breakout**: 20-day resistance breakout with volume surge > 1.3x.
  - **Oversold Trend Bounce**: RSI dipping < 40 in a stock trading above its 200 EMA.
- Calculates exact **Entry**, **ATR Stop Loss**, **Target 1 (1:2 RR)**, and **Target 2 (1:3 RR)**.
- Ranks opportunities by Quality Score (0–100).

### 2. 📈 Deep Dive & Interactive Chart
- Interactive Plotly multi-pane candlestick chart:
  - Price with 20 EMA, 50 EMA, 200 EMA ribbons and SuperTrend.
  - Plotted Stop Loss and Target price lines.
  - Volume subplot with 20-day volume moving average.
  - RSI (14) momentum oscillator.
- **AI Thesis & Review**: Catalysts, invalidation levels, downside risks, and step-by-step roadmap.
- One-click simulation: Adds trade directly to your Paper Portfolio.

### 3. 🛡️ Risk & Position Sizer
- Calculates exact number of shares to buy so your rupee risk never exceeds your pre-set limit (e.g. ₹5,000 max loss on ₹5,00,000 account).
- Displays total capital requirement, allocation percentage, and risk-reward ratio.
- Caps maximum single-stock exposure at 25% of portfolio to prevent concentration risk.

### 4. 💼 Paper Portfolio & Trade Journal
- Simulates swing trades with zero financial risk.
- Tracks live P&L, Hit Targets, Win Rate %, and Profit Factor.
- Allows closing trades manually or testing strategies across market cycles.

### 5. 📊 NIFTY Market Breadth
- Gauges broad market health: % of stocks above 20 EMA, 50 EMA, and 200 EMA.
- Evaluates NIFTY 50 trend regime (Bullish / Choppy / Bearish) so you never enter aggressive longs during market corrections.

---

## 🤖 AI Engine

The assistant supports two analysis modes:
1. **Built-in Offline Quantitative Engine (Default)**: Fully offline deterministic thesis generation using multi-factor technical criteria, ATR volatility calculations, and regime alignment.
2. **Gemini LLM (Optional)**: Enter your `GEMINI_API_KEY` in the sidebar or export `export GEMINI_API_KEY="your-key"` to generate dynamic LLM trade theses.
