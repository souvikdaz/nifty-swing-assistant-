import os
import streamlit as st
import pandas as pd
from datetime import datetime

from engine.data_fetcher import load_stock_universe, fetch_ticker_data, fetch_batch_stocks, get_nifty_regime
from engine.screener import screen_nifty_universe
from engine.risk_manager import RiskManager
from engine.ai_analyst import get_ai_trade_analysis
from engine.charts import create_swing_chart
from engine.paper_trader import (
    load_portfolio,
    open_paper_trade,
    close_paper_trade,
    update_open_trades_with_live_prices,
    get_portfolio_metrics,
    reset_paper_portfolio
)

# Page configuration
st.set_page_config(
    page_title="NIFTY Swing AI Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e222d;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #29b6f6;
        margin-bottom: 12px;
    }
    .bullish-badge {
        background-color: #1b5e20;
        color: #a5d6a7;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .bearish-badge {
        background-color: #b71c1c;
        color: #ffcdd2;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .caution-badge {
        background-color: #f57f17;
        color: #fff9c4;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .risk-alert {
        background-color: #2b1b17;
        border-left: 4px solid #ff5252;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Cache stock universe
universe = load_stock_universe()
nifty_stocks = universe.get("stocks", [])
stock_symbols = [s["symbol"] for s in nifty_stocks]

# Initialize Session State
if "selected_symbol" not in st.session_state:
    st.session_state["selected_symbol"] = "RELIANCE.NS"
if "gemini_api_key" not in st.session_state:
    secret_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            secret_key = str(st.secrets["GEMINI_API_KEY"])
    except Exception:
        pass
    st.session_state["gemini_api_key"] = secret_key or os.environ.get("GEMINI_API_KEY", "")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ NIFTY Swing AI")
    st.caption("Capital-Preservation Swing Trading System")
    
    st.markdown("---")
    st.subheader("⚙️ Risk Controls")
    account_capital = st.number_input(
        "Total Portfolio Capital (₹)",
        min_value=10000.0,
        max_value=100000000.0,
        value=500000.0,
        step=25000.0,
        help="Used to strictly calculate maximum position sizes and risk limits."
    )
    
    risk_pct = st.slider(
        "Max Risk per Trade (%)",
        min_value=0.5,
        max_value=2.5,
        value=1.0,
        step=0.25,
        help="Golden Rule: Keep risk at 1% to 1.5% to avoid drawdowns."
    )
    
    st.caption(f"Max Rupee Loss per Trade: **₹{(account_capital * (risk_pct/100)):,.0f}**")
    
    st.markdown("---")
    st.subheader("🤖 AI Integration (Optional)")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state["gemini_api_key"],
        type="password",
        help="Optional. Leave blank to use built-in offline quantitative reasoning."
    )
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input

    st.markdown("---")
    if st.button("🔄 Refresh Market Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Zero-Loss Trading Truth:**
    > No system can win 100% of trades. We preserve capital by:
    > 1. Keeping losers tiny (max 1%).
    > 2. Booking 1:2+ RR on winners.
    > 3. Moving stop to breakeven quickly.
    """)

# --- LOAD MARKET DATA ---
with st.spinner("Fetching live NIFTY 50 and constituent data..."):
    nifty_regime = get_nifty_regime()
    stocks_data = fetch_batch_stocks(stock_symbols, period="1y")

# Screen opportunities
opportunities = screen_nifty_universe(stocks_data, nifty_stocks)

# Update Paper Portfolio with latest prices
latest_prices = {sym: df.iloc[-1]['Close'] for sym, df in stocks_data.items() if not df.empty}
portfolio = update_open_trades_with_live_prices(latest_prices)
portfolio_metrics = get_portfolio_metrics(portfolio)

# --- HEADER STATUS BAR ---
col_head1, col_head2, col_head3, col_head4 = st.columns([2.5, 2, 2, 2])

with col_head1:
    trend_badge_class = "bullish-badge" if "Bullish" in nifty_regime["status"] else ("bearish-badge" if "Bearish" in nifty_regime["status"] else "caution-badge")
    st.markdown(f"### NIFTY 50: **₹{nifty_regime['close']:,}** ({nifty_regime['change_pct']:+.2f}%)")
    st.markdown(f"Regime: <span class='{trend_badge_class}'>{nifty_regime['status']}</span>", unsafe_allow_html=True)

with col_head2:
    st.metric("NIFTY 20 EMA", f"₹{nifty_regime['ema_20']:,}")
    st.caption(f"SuperTrend: {nifty_regime['supertrend_direction']}")

with col_head3:
    st.metric("Qualified Swing Setups", f"{len(opportunities)} / {len(nifty_stocks)}")
    st.caption("Screened with 1:2+ RR filter")

with col_head4:
    st.metric("Paper Net Worth", f"₹{portfolio_metrics['current_net_worth']:,.2f}", f"{portfolio_metrics['total_pnl']:+,.2f} ({portfolio_metrics['total_pnl_pct']:+.1f}%)")
    st.caption(f"{portfolio_metrics['open_trades_count']} Active Swings")

# Alert on Market Stance
if "Bearish" in nifty_regime["status"]:
    st.markdown(f"""
    <div class="risk-alert">
        <strong>⚠️ Market Warning:</strong> NIFTY 50 is currently in a <strong>{nifty_regime['status']}</strong>.
        {nifty_regime['stance']}. Long swing setups carry higher risk of failure. Reduce position size by 50% or wait.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- MAIN TABS ---
tab_screener, tab_deepdive, tab_risk, tab_paper, tab_regime = st.tabs([
    "🎯 Swing Screener & Ideas",
    "📈 Deep Dive & Interactive Chart",
    "🛡️ Risk & Position Sizer",
    "💼 Paper Portfolio & Journal",
    "📊 NIFTY Market Breadth"
])

# ==========================================
# TAB 1: SWING SCREENER
# ==========================================
with tab_screener:
    st.subheader("🎯 High-Probability NIFTY Swing Setups")
    st.markdown("Every candidate is filtered for **trend alignment**, **volume confirmation**, and strict **1:2+ Risk-Reward**.")

    if not opportunities:
        st.info("No stocks currently meet the strict swing criteria under current market conditions. Capital preservation rule: When no safe setup exists, stay in cash.")
    else:
        # Filter controls
        f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
        with f_col1:
            all_sectors = sorted(list(set(s["sector"] for s in opportunities)))
            sector_filter = st.multiselect("Filter by Sector", options=all_sectors, default=all_sectors)
        with f_col2:
            all_setups = sorted(list(set(s["setup"] for s in opportunities)))
            setup_filter = st.multiselect("Filter by Setup Type", options=all_setups, default=all_setups)
        with f_col3:
            min_score = st.slider("Minimum Quality Score", min_value=30, max_value=95, value=50, step=5)

        filtered_opps = [
            o for o in opportunities
            if o["sector"] in sector_filter and o["setup"] in setup_filter and o["score"] >= min_score
        ]

        st.caption(f"Showing **{len(filtered_opps)}** matching swing opportunities:")

        # Summary Table
        table_rows = []
        for o in filtered_opps:
            table_rows.append({
                "Symbol": o["symbol"],
                "Stock Name": o["name"],
                "Sector": o["sector"],
                "Setup Type": o["setup"],
                "Quality Score": f"{o['score']}/100",
                "Current Price": f"₹{o['close']:.2f}",
                "Stop Loss": f"₹{o['stop_loss']:.2f}",
                "Risk %": f"{o['risk_pct']:.2f}%",
                "Target 1 (1:2)": f"₹{o['target_1']:.2f} (+{o['target_1_gain']}%)",
                "Target 2 (1:3)": f"₹{o['target_2']:.2f} (+{o['target_2_gain']}%)",
                "RSI": o["rsi"],
                "Vol Surge": f"{o['vol_ratio']:.1f}x"
            })

        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("### Top Ranked Setups for Detailed Review")
        top_cards = filtered_opps[:3]
        cols = st.columns(len(top_cards)) if top_cards else []

        for idx, col in enumerate(cols):
            cand = top_cards[idx]
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{cand['name']} ({cand['symbol']})</h4>
                    <p style="color: #64b5f6; font-weight: bold; margin-bottom: 4px;">{cand['setup']}</p>
                    <p>Score: <strong>{cand['score']}/100</strong> | Sector: {cand['sector']}</p>
                    <hr style="margin: 8px 0;"/>
                    <p>Price: <strong>₹{cand['close']:.2f}</strong></p>
                    <p style="color: #ef5350;">Stop Loss: <strong>₹{cand['stop_loss']:.2f}</strong> (-{cand['risk_pct']}%)</p>
                    <p style="color: #26a69a;">Target 1: <strong>₹{cand['target_1']:.2f}</strong> (+{cand['target_1_gain']}%)</p>
                    <p style="color: #69f0ae;">Target 2: <strong>₹{cand['target_2']:.2f}</strong> (+{cand['target_2_gain']}%)</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Analyze {cand['symbol']}", key=f"btn_analyze_{cand['symbol']}", use_container_width=True):
                    st.session_state["selected_symbol"] = cand["symbol"]
                    st.rerun()

# ==========================================
# TAB 2: DEEP DIVE & CHART
# ==========================================
with tab_deepdive:
    selected_sym = st.selectbox(
        "Select Stock for Deep Technical & AI Analysis",
        options=stock_symbols,
        index=stock_symbols.index(st.session_state["selected_symbol"]) if st.session_state["selected_symbol"] in stock_symbols else 0
    )
    st.session_state["selected_symbol"] = selected_sym

    stock_meta = next((s for s in nifty_stocks if s["symbol"] == selected_sym), {"name": selected_sym, "sector": "General"})
    df_stock = stocks_data.get(selected_sym)

    if df_stock is None or df_stock.empty:
        st.warning(f"Could not load historical data for {selected_sym}.")
    else:
        # Check if stock has qualified setup
        setup_meta = next((o for o in opportunities if o["symbol"] == selected_sym), None)

        col_chart, col_ai = st.columns([1.6, 1.0])

        with col_chart:
            st.subheader(f"📊 Chart: {stock_meta['name']} ({selected_sym})")
            fig = create_swing_chart(df_stock, selected_sym, stock_meta["name"], setup=setup_meta)
            st.plotly_chart(fig, use_container_width=True)

        with col_ai:
            st.subheader("🤖 AI Thesis & Risk Review")

            if setup_meta:
                ai_report = get_ai_trade_analysis(setup_meta, nifty_regime, st.session_state.get("gemini_api_key"))
                
                st.markdown(f"**Conviction Level:** {ai_report.get('conviction_badge', '🟡')} **{ai_report.get('conviction', 'Evaluated')}**")
                st.info(ai_report.get("guidance", "Manage position size strictly."))

                with st.expander("📌 Key Catalysts & Technical Signals", expanded=True):
                    for c in ai_report.get("catalysts", []):
                        st.markdown(f"- {c}")

                with st.expander("🚨 Invalidation & Downside Risks", expanded=True):
                    for r in ai_report.get("risks", []):
                        st.markdown(f"- {r}")

                with st.expander("📋 Execution & Profit-Booking Roadmap", expanded=False):
                    for a in ai_report.get("action_plan", []):
                        st.markdown(f"{a}")

                # Calculate suggested shares for current account settings
                pos_calc = RiskManager.calculate_position(
                    account_capital=account_capital,
                    risk_per_trade_pct=risk_pct,
                    entry_price=setup_meta["close"],
                    stop_loss_price=setup_meta["stop_loss"]
                )

                if pos_calc["valid"]:
                    st.markdown("---")
                    st.markdown("#### ⚡ Paper Trade Simulation")
                    st.write(f"Calculated Shares (1% Risk): **{pos_calc['shares_to_buy']} shares** (Total Capital: ₹{pos_calc['total_capital_required']:,.2f})")
                    st.write(f"Max Rupee Risk: **₹{pos_calc['maximum_loss_rupees']:,.2f}**")

                    if st.button("➕ Open Paper Trade Now", use_container_width=True, type="primary"):
                        res = open_paper_trade(
                            symbol=selected_sym,
                            name=stock_meta["name"],
                            entry_price=setup_meta["close"],
                            stop_loss=setup_meta["stop_loss"],
                            target_1=setup_meta["target_1"],
                            target_2=setup_meta["target_2"],
                            quantity=pos_calc["shares_to_buy"]
                        )
                        if res["success"]:
                            st.success(f"Paper trade opened for {pos_calc['shares_to_buy']} shares of {stock_meta['name']}!")
                            st.rerun()
                        else:
                            st.error(res["message"])
            else:
                st.warning("⚠️ This stock does not currently qualify for a safe swing entry under quantitative criteria.")
                st.write("Reason: Either trend momentum is weak, distance to 20/50 EMA is too wide, or the risk-to-reward ratio is below 1:2.")
                st.caption("Do not force trades when setup rules are not met.")

# ==========================================
# TAB 3: RISK & POSITION SIZER
# ==========================================
with tab_risk:
    st.subheader("🛡️ Institutional Position Sizing & Loss Prevention Calculator")
    st.markdown("""
    The only guaranteed way to avoid devastating losses is **Fixed-Fractional Position Sizing**.
    You decide your rupee loss **before** entering the trade, and adjust share quantity accordingly.
    """)

    rc1, rc2 = st.columns([1.2, 1.8])

    with rc1:
        st.markdown("#### Input Parameters")
        calc_capital = st.number_input("Account Capital (₹)", value=account_capital, step=25000.0)
        calc_risk_pct = st.slider("Risk Limit per Trade (%)", min_value=0.5, max_value=2.5, value=risk_pct, step=0.25)
        calc_entry = st.number_input("Entry Price (₹)", min_value=1.0, value=1500.0, step=10.0)
        calc_sl = st.number_input("Stop-Loss Price (₹)", min_value=0.5, value=1450.0, step=10.0)
        calc_t1 = st.number_input("Target 1 Price (₹)", min_value=calc_entry, value=1600.0, step=10.0)

        calc_result = RiskManager.calculate_position(calc_capital, calc_risk_pct, calc_entry, calc_sl)

    with rc2:
        st.markdown("#### Position Sizing Output")
        if calc_result["valid"]:
            m1, m2, m3 = st.columns(3)
            m1.metric("Shares to Buy", f"{calc_result['shares_to_buy']}")
            m2.metric("Max Rupee Loss", f"₹{calc_result['maximum_loss_rupees']:,.2f}")
            m3.metric("Trade Capital", f"₹{calc_result['total_capital_required']:,.2f}")

            st.write(f"- Portfolio Risk: **{calc_result['maximum_loss_of_portfolio_pct']:.2f}%** of account capital")
            st.write(f"- Stock Stop Loss Distance: **{calc_result['risk_percentage_on_stock']:.2f}%**")
            st.write(f"- Allocation Percentage: **{calc_result['capital_allocation_pct']:.2f}%** of total portfolio")

            if calc_result.get("capped_by_concentration_limit"):
                st.info("ℹ️ Position size was capped at 25% of total capital to prevent overconcentration in a single stock.")

            # Expected Profit calculation
            gain_t1 = (calc_t1 - calc_entry) * calc_result['shares_to_buy']
            reward_ratio = (calc_t1 - calc_entry) / (calc_entry - calc_sl)
            st.markdown(f"""
            - Expected Profit at Target 1: **₹{gain_t1:,.2f}**
            - Risk-to-Reward Ratio: **1 : {reward_ratio:.2f}**
            """)
        else:
            st.error(calc_result["error"])

        st.markdown("---")
        st.markdown("#### 📜 The 5 Golden Rules for Zero-Loss Mindset")
        rules = RiskManager.get_golden_rules()
        for r in rules:
            st.markdown(f"- **{r['rule']}**: {r['desc']}")

# ==========================================
# TAB 4: PAPER PORTFOLIO & JOURNAL
# ==========================================
with tab_paper:
    st.subheader("💼 Paper Trading Portfolio & Live Performance Tracker")
    st.caption("Practice executing setups with zero real-money risk. Validate your discipline over 20+ trades before deploying real money.")

    # Top metrics
    pm1, pm2, pm3, pm4, pm5 = st.columns(5)
    pm1.metric("Cash Balance", f"₹{portfolio_metrics['cash_balance']:,.2f}")
    pm2.metric("Total Net Worth", f"₹{portfolio_metrics['current_net_worth']:,.2f}")
    pm3.metric("Realized P&L", f"₹{portfolio_metrics['total_realized_pnl']:+,.2f}")
    pm4.metric("Win Rate", f"{portfolio_metrics['win_rate']}%")
    pm5.metric("Profit Factor", f"{portfolio_metrics['profit_factor']}")

    st.markdown("### Open Swing Trades")
    open_trades = portfolio.get("open_trades", [])

    if not open_trades:
        st.info("No open paper trades. Go to the 'Swing Screener' or 'Deep Dive' tab to simulate a swing trade.")
    else:
        for trade in open_trades:
            t_col1, t_col2, t_col3, t_col4, t_col5, t_col6 = st.columns([2, 1.5, 1.5, 1.5, 2, 1.5])
            with t_col1:
                st.markdown(f"**{trade['name']}** ({trade['symbol']})")
                st.caption(f"Entry Date: {trade['entry_date']}")
            with t_col2:
                st.write(f"Entry: ₹{trade['entry_price']:.2f}")
                st.write(f"Current: ₹{trade['current_price']:.2f}")
            with t_col3:
                st.write(f"Stop: ₹{trade['stop_loss']:.2f}")
                st.write(f"Target 1: ₹{trade['target_1']:.2f}")
            with t_col4:
                st.write(f"Qty: {trade['quantity']}")
                st.write(f"Cost: ₹{trade['cost_basis']:,.2f}")
            with t_col5:
                pnl = trade['unrealized_pnl']
                pnl_pct = trade['unrealized_pnl_pct']
                pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
                st.markdown(f"<span style='color:{pnl_color}; font-weight:bold; font-size:1.1rem;'>₹{pnl:+,.2f} ({pnl_pct:+.2f}%)</span>", unsafe_allow_html=True)
            with t_col6:
                if st.button("Close Trade", key=f"close_{trade['id']}"):
                    close_paper_trade(trade['id'], trade['current_price'], "Manual User Exit")
                    st.success(f"Closed {trade['symbol']} trade.")
                    st.rerun()
            st.markdown("<hr style='margin: 4px 0;'/>", unsafe_allow_html=True)

    st.markdown("### Closed Trades History")
    closed_trades = portfolio.get("closed_trades", [])
    if closed_trades:
        c_table = []
        for ct in reversed(closed_trades):
            c_table.append({
                "Stock": ct["name"],
                "Symbol": ct["symbol"],
                "Entry Date": ct["entry_date"],
                "Exit Date": ct.get("exit_date", "N/A"),
                "Entry Price": f"₹{ct['entry_price']:.2f}",
                "Exit Price": f"₹{ct['exit_price']:.2f}",
                "Quantity": ct["quantity"],
                "Realized P&L (₹)": f"₹{ct['realized_pnl']:+,.2f}",
                "P&L %": f"{ct['pnl_pct']:+.2f}%",
                "Exit Reason": ct.get("exit_reason", "Manual")
            })
        st.dataframe(pd.DataFrame(c_table), use_container_width=True, hide_index=True)
    else:
        st.caption("No closed trades recorded yet.")

    st.markdown("---")
    with st.expander("⚠️ Danger Zone: Reset Portfolio"):
        if st.button("Reset Paper Portfolio to Initial Balance"):
            reset_paper_portfolio(account_capital)
            st.success("Paper portfolio reset!")
            st.rerun()

# ==========================================
# TAB 5: MARKET REGIME & BREADTH
# ==========================================
with tab_regime:
    st.subheader("📊 NIFTY 50 Market Breadth & Health")
    st.markdown("Swing trading success rate is 3x higher when market breadth is supportive.")

    # Compute breadth
    stocks_above_20ema = 0
    stocks_above_50ema = 0
    stocks_above_200ema = 0
    total_valid = 0

    for s, df in stocks_data.items():
        if df is not None and not df.empty and len(df) >= 50:
            total_valid += 1
            last_c = df.iloc[-1]['Close']
            if last_c > df.iloc[-1].get('EMA_20', last_c):
                stocks_above_20ema += 1
            if last_c > df.iloc[-1].get('EMA_50', last_c):
                stocks_above_50ema += 1
            if 'EMA_200' in df.iloc[-1] and not pd.isna(df.iloc[-1]['EMA_200']) and last_c > df.iloc[-1]['EMA_200']:
                stocks_above_200ema += 1

    if total_valid > 0:
        b1, b2, b3 = st.columns(3)
        b1.metric("% Above 20 EMA (Short-Term)", f"{(stocks_above_20ema/total_valid)*100:.1f}%")
        b2.metric("% Above 50 EMA (Medium-Term)", f"{(stocks_above_50ema/total_valid)*100:.1f}%")
        b3.metric("% Above 200 EMA (Long-Term)", f"{(stocks_above_200ema/total_valid)*100:.1f}%")

    st.markdown("#### Sectoral Distribution of Top NIFTY Constituents")
    sector_counts = {}
    for item in nifty_stocks:
        sec = item.get("sector", "Other")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    sec_df = pd.DataFrame([{"Sector": k, "Stock Count": v} for k, v in sector_counts.items()])
    st.bar_chart(sec_df.set_index("Sector"))
