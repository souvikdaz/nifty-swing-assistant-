import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_swing_chart(df: pd.DataFrame, symbol: str, stock_name: str, setup: dict = None) -> go.Figure:
    """
    Builds an interactive professional financial chart with Candlesticks,
    Moving Averages, SuperTrend, Volume, RSI, and MACD.
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(title="No chart data available")
        return fig

    # Keep last 120 trading days for clear swing context
    df_plot = df.iloc[-120:].copy()

    # Create 3-row subplot: 1. Price (60%), 2. Volume (15%), 3. RSI (25%)
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.60, 0.15, 0.25],
        subplot_titles=(f"{stock_name} ({symbol}) - Daily Swing Chart", "Volume", "RSI (14)")
    )

    # 1. Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df_plot.index,
            open=df_plot['Open'],
            high=df_plot['High'],
            low=df_plot['Low'],
            close=df_plot['Close'],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350"
        ),
        row=1, col=1
    )

    # 2. Moving Average Overlays
    if 'EMA_20' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_20'], line=dict(color="#29b6f6", width=1.5), name="EMA 20"), row=1, col=1)
    if 'EMA_50' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_50'], line=dict(color="#ffa726", width=1.5), name="EMA 50"), row=1, col=1)
    if 'EMA_200' in df_plot.columns and not df_plot['EMA_200'].isna().all():
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['EMA_200'], line=dict(color="#ab47bc", width=2, dash="dot"), name="EMA 200"), row=1, col=1)

    # 3. SuperTrend
    if 'SuperTrend' in df_plot.columns:
        fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['SuperTrend'], line=dict(color="#00e676", width=1, dash="dash"), name="SuperTrend"), row=1, col=1)

    # Setup Trade Lines (Stop-Loss and Targets)
    if setup:
        entry_p = setup.get("close")
        sl_p = setup.get("stop_loss")
        t1_p = setup.get("target_1")
        t2_p = setup.get("target_2")

        # Entry Horizontal Line
        fig.add_hline(y=entry_p, line=dict(color="#ffffff", width=1.2, dash="dash"),
                      annotation_text=f" Entry: ₹{entry_p}", annotation_position="top left", row=1, col=1)
        # Stop Loss Horizontal Line
        fig.add_hline(y=sl_p, line=dict(color="#ff5252", width=1.5, dash="dash"),
                      annotation_text=f" Stop Loss: ₹{sl_p}", annotation_position="bottom left", row=1, col=1)
        # Target 1
        fig.add_hline(y=t1_p, line=dict(color="#00e676", width=1.5, dash="dash"),
                      annotation_text=f" Target 1 (1:2): ₹{t1_p}", annotation_position="top left", row=1, col=1)
        # Target 2
        fig.add_hline(y=t2_p, line=dict(color="#69f0ae", width=1.5, dash="dot"),
                      annotation_text=f" Target 2 (1:3): ₹{t2_p}", annotation_position="top left", row=1, col=1)

    # 4. Volume Subplot
    vol_colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df_plot['Close'], df_plot['Open'])]
    fig.add_trace(
        go.Bar(x=df_plot.index, y=df_plot['Volume'], marker_color=vol_colors, name="Volume", showlegend=False),
        row=2, col=1
    )
    if 'Vol_SMA_20' in df_plot.columns:
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot['Vol_SMA_20'], line=dict(color="#ffeb3b", width=1), name="20 Vol SMA"),
            row=2, col=1
        )

    # 5. RSI Subplot
    if 'RSI' in df_plot.columns:
        fig.add_trace(
            go.Scatter(x=df_plot.index, y=df_plot['RSI'], line=dict(color="#ba68c8", width=1.8), name="RSI (14)"),
            row=3, col=1
        )
        fig.add_hline(y=70, line=dict(color="#ef5350", width=1, dash="dot"), row=3, col=1)
        fig.add_hline(y=30, line=dict(color="#26a69a", width=1, dash="dot"), row=3, col=1)
        fig.add_hline(y=50, line=dict(color="#78909c", width=0.8, dash="dash"), row=3, col=1)

    # Layout styling
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=720,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Vol", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[10, 90], row=3, col=1)

    return fig
