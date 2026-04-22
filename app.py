"""
Nifty 50 Stock Screener — Streamlit App

A production-ready web app for screening NSE Nifty 50 stocks using
technical indicators (RSI, SMA, MACD, Volume).

Run with: streamlit run app.py
"""

import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import fetch_stock_data
from screener import SCAN_PRESETS, run_preset_scan, run_custom_screener, load_and_calculate_all
from tickers import NIFTY50_TICKERS


# --------------------------------------------------------------------------
# Page Configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Nifty 50 Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------
# Cached Data Loader (fetches ONCE per session, cached for 1 hour)
# --------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def _get_all_indicators():
    """Fetch all 50 stocks and calculate indicators. Cached for 1 hour."""
    return load_and_calculate_all()


# --------------------------------------------------------------------------
# Helper: Color-coded RSI styling
# --------------------------------------------------------------------------
def style_rsi(val):
    """
    Color RSI values:
        < 30  → green (oversold / potential buy)
        > 70  → red   (overbought / potential sell)
        else  → gray  (neutral)
    """
    if pd.isna(val):
        return ""
    if val < 30:
        return "color: #00D4AA; font-weight: bold;"
    elif val > 70:
        return "color: #FF6B6B; font-weight: bold;"
    return "color: #888888;"


def style_bool(val):
    """Color True/False values."""
    if val is True:
        return "color: #00D4AA; font-weight: bold;"
    elif val is False:
        return "color: #FF6B6B;"
    return ""


# --------------------------------------------------------------------------
# Helper: Mini Price Chart
# --------------------------------------------------------------------------
def render_mini_chart(ticker: str):
    """Render a Plotly line chart showing price + SMA50 + SMA200."""
    df = fetch_stock_data(ticker, period_days=180)
    if df is None or df.empty:
        st.warning(f"No chart data for {ticker}")
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines", name="Price",
        line=dict(color="#00D4AA", width=2),
    ))

    sma50 = df["Close"].rolling(window=50).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=sma50,
        mode="lines", name="SMA 50",
        line=dict(color="#FFD93D", width=1.5, dash="dash"),
    ))

    sma200 = df["Close"].rolling(window=200).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=sma200,
        mode="lines", name="SMA 200",
        line=dict(color="#FF6B6B", width=1.5, dash="dot"),
    ))

    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=None,
        yaxis_title="Price (₹)",
    )

    st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}")


# --------------------------------------------------------------------------
# Main App
# --------------------------------------------------------------------------
def main():
    # ── Header ──────────────────────────────────────────────────────────
    st.title("📈 Nifty 50 Stock Screener")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")

    # ── Load Data ONCE (cached for 1 hour) ──────────────────────────────
    if "indicators_df" not in st.session_state:
        progress_text = st.empty()
        progress_bar = st.progress(0)

        def update_progress(current, total, ticker):
            progress_text.text(f"Loading {ticker}... ({current}/{total})")
            progress_bar.progress(current / total)

        indicators_df, failed_tickers = load_and_calculate_all(
            progress_callback=update_progress
        )

        progress_text.empty()
        progress_bar.empty()

        st.session_state.indicators_df = indicators_df
        st.session_state.failed_tickers = failed_tickers

    indicators_df = st.session_state.indicators_df
    failed_tickers = st.session_state.failed_tickers

    if indicators_df.empty:
        st.error("❌ Failed to load stock data. Please refresh the page.")
        return

    # ── Sidebar ─────────────────────────────────────────────────────────
    st.sidebar.header("🔍 Scan Settings")

    scan_mode = st.sidebar.radio(
        "Select scan mode:",
        ["Preset Scans", "Custom Filters"],
        index=0,
    )

    if scan_mode == "Preset Scans":
        preset_name = st.sidebar.selectbox(
            "Choose a preset scan:",
            list(SCAN_PRESETS.keys()),
            index=0,
        )
        st.sidebar.caption(SCAN_PRESETS[preset_name]["description"])
        run_button = st.sidebar.button("▶️ Run Preset Scan", type="primary")
        filters = {"preset": preset_name}

    else:
        st.sidebar.subheader("Custom Filters")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            rsi_min = st.number_input("RSI Min", 0.0, 100.0, 0.0, 5.0)
        with col2:
            rsi_max = st.number_input("RSI Max", 0.0, 100.0, 100.0, 5.0)

        price_above_sma50 = st.sidebar.toggle("Price > SMA 50", value=False)
        price_above_sma200 = st.sidebar.toggle("Price > SMA 200", value=False)
        macd_bullish = st.sidebar.toggle("MACD Bullish", value=False)
        volume_spike = st.sidebar.toggle("Volume Spike", value=False)
        pct_from_52w_low_max = st.sidebar.slider(
            "Max % from 52W Low", 0.0, 100.0, 100.0, 5.0
        )

        run_button = st.sidebar.button("▶️ Run Custom Scan", type="primary")
        filters = {
            "rsi_min": rsi_min if rsi_min > 0 else None,
            "rsi_max": rsi_max if rsi_max < 100 else None,
            "price_above_sma50": price_above_sma50,
            "price_above_sma200": price_above_sma200,
            "macd_bullish": macd_bullish,
            "volume_spike": volume_spike,
            "pct_from_52w_low_max": pct_from_52w_low_max if pct_from_52w_low_max < 100 else None,
        }

    # ── Main Content ────────────────────────────────────────────────────
    if not run_button:
        # Show market overview stats + prompt BEFORE any scan is run
        total = len(indicators_df)
        above_200sma = (indicators_df["price"] > indicators_df["sma200"]).sum()
        oversold = (indicators_df["rsi"] < 30).sum()
        overbought = (indicators_df["rsi"] > 70).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nifty 50 Stocks", f"{total}/50")
        c2.metric("Above 200-SMA", f"{above_200sma}", f"{above_200sma/total*100:.0f}%")
        c3.metric("Oversold (RSI<30)", f"{oversold}", delta=None, delta_color="inverse")
        c4.metric("Overbought (RSI>70)", f"{overbought}", delta=None, delta_color="inverse")

        if failed_tickers:
            st.warning(f"⚠️ Failed to load {len(failed_tickers)} tickers: {', '.join(failed_tickers[:5])}{'...' if len(failed_tickers) > 5 else ''}")

        st.info("👈 Choose a preset scan or custom filters, then click **Run Scan**.")
        return

    # ── Run the Scan (NO re-fetching — just filters existing data) ──────
    start_time = time.time()

    if scan_mode == "Preset Scans":
        result_df, scan_failed, total_scanned = run_preset_scan(
            filters["preset"],
            indicators_df=indicators_df,
            failed_tickers=failed_tickers,
        )
    else:
        result_df, scan_failed, total_scanned = run_custom_screener(
            indicators_df=indicators_df,
            failed_tickers=failed_tickers,
            **filters,
        )

    elapsed = time.time() - start_time

    # ── Scan Results Metrics ────────────────────────────────────────────
    matched = len(result_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Stocks Matched", f"{matched}/{total_scanned}")
    c2.metric("Scan Time", f"{elapsed:.2f}s")
    c3.metric("Failed Tickers", len(scan_failed))

    if matched == 0:
        st.info("No stocks matched your criteria. Try relaxing the filters.")
        return

    # ── Results Table ───────────────────────────────────────────────────
    st.subheader("📋 Scan Results")

    if "rsi" in result_df.columns:
        result_df = result_df.sort_values("rsi", ascending=True, na_position="last")

    display_cols = ["ticker", "price", "rsi", "sma50", "sma200", "macd_bullish", "volume_spike", "pct_from_52w_high", "pct_from_52w_low"]
    display_cols = [c for c in display_cols if c in result_df.columns]

    styled_df = result_df[display_cols].style\
        .map(style_rsi, subset=["rsi"])\
        .map(style_bool, subset=["macd_bullish", "volume_spike"])\
        .format({
            "price": "₹{:,.2f}",
            "rsi": "{:.1f}",
            "sma50": "₹{:,.2f}",
            "sma200": "₹{:,.2f}",
            "pct_from_52w_high": "{:.1f}%",
            "pct_from_52w_low": "{:.1f}%",
        })\
        .set_properties(**{"text-align": "center"})

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ── CSV Export ──────────────────────────────────────────────────────
    csv = result_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download Results as CSV",
        data=csv,
        file_name=f"nifty50_screener_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    # ── Mini Charts ─────────────────────────────────────────────────────
    st.subheader("📊 Price Charts")
    st.caption("Expand rows below to view charts")

    for _, row in result_df.iterrows():
        ticker = row["ticker"]
        with st.expander(f"📈 {ticker} — ₹{row['price']:.2f} | RSI: {row['rsi']:.1f}"):
            render_mini_chart(ticker)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("SMA 50", f"₹{row['sma50']:,.2f}" if pd.notna(row['sma50']) else "N/A")
            c2.metric("SMA 200", f"₹{row['sma200']:,.2f}" if pd.notna(row['sma200']) else "N/A")
            c3.metric("From 52W High", f"{row['pct_from_52w_high']:.1f}%" if pd.notna(row['pct_from_52w_high']) else "N/A")
            c4.metric("From 52W Low", f"{row['pct_from_52w_low']:.1f}%" if pd.notna(row['pct_from_52w_low']) else "N/A")


if __name__ == "__main__":
    main()
