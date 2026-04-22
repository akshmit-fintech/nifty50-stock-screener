"""
Technical indicator calculations for Nifty 50 stock screener.

Uses the `ta` (Technical Analysis) library for robust, well-tested indicators.
Each function includes educational comments explaining the finance concepts.

References:
    - RSI: Relative Strength Index (J. Welles Wilder, 1978)
    - SMA: Simple Moving Average — trend smoothing
    - MACD: Moving Average Convergence Divergence (Gerald Appel, 1979)
"""

from typing import Optional
import pandas as pd
import numpy as np

# `ta` library provides pandas-native technical indicators
try:
    from ta.momentum import RSIIndicator
    from ta.trend import SMAIndicator, MACD
except ImportError:
    raise ImportError(
        "The 'ta' library is required. Install it: pip install ta>=0.11.0"
    )


def calculate_indicators(df: pd.DataFrame) -> Optional[dict]:
    """
    Calculate all technical indicators for a single stock's OHLCV data.

    Args:
        df: DataFrame with columns [Open, High, Low, Close, Volume]
            Must have at least 200 rows for full indicator set.

    Returns:
        Dict of indicator values, or None if calculation fails.
    """
    if df is None or len(df) < 50:
        # Need at least 50 days for SMA-50. RSI(14) needs 14.
        return None

    close = df["Close"]
    volume = df["Volume"]

    # ------------------------------------------------------------------
    # Latest price (most recent closing price)
    # ------------------------------------------------------------------
    latest_price = float(close.iloc[-1])

    # ------------------------------------------------------------------
    # RSI(14) — Relative Strength Index
    # ------------------------------------------------------------------
    # RSI measures the speed and magnitude of recent price changes.
    # It oscillates between 0 and 100.
    #
    # Interpretation:
    #   RSI < 30  → Oversold (potential buying opportunity)
    #   RSI > 70  → Overbought (potential selling opportunity)
    #   RSI ≈ 50  → Neutral momentum
    #
    # Why 14 periods? Wilder's default — balances sensitivity vs noise.
    # ------------------------------------------------------------------
    try:
        rsi = float(RSIIndicator(close=close, window=14).rsi().iloc[-1])
    except Exception:
        rsi = None

    # ------------------------------------------------------------------
    # SMA 50 — 50-Day Simple Moving Average
    # ------------------------------------------------------------------
    # SMA smooths price data by averaging closing prices over N periods.
    # It reveals the underlying trend by filtering out daily noise.
    #
    # Interpretation:
    #   Price > SMA-50  → Short-to-medium term uptrend
    #   Price < SMA-50  → Short-to-medium term downtrend
    #
    # Traders watch for "Golden Cross" (SMA-50 crossing above SMA-200)
    # as a bullish long-term signal.
    # ------------------------------------------------------------------
    try:
        sma50_series = SMAIndicator(close=close, window=50).sma_indicator()
        sma50 = float(sma50_series.iloc[-1])
    except Exception:
        sma50 = None

    # ------------------------------------------------------------------
    # SMA 200 — 200-Day Simple Moving Average
    # ------------------------------------------------------------------
    # The 200-SMA is the "big picture" trend indicator.
    # Institutions and long-term investors use it as a macro filter.
    #
    # Interpretation:
    #   Price > SMA-200  → Long-term bull market (" Stage 2 uptrend")
    #   Price < SMA-200  → Long-term bear market / consolidation
    #
    # Many traders won't buy stocks below 200-SMA — it's a risk-off signal.
    # ------------------------------------------------------------------
    try:
        sma200_series = SMAIndicator(close=close, window=200).sma_indicator()
        sma200 = float(sma200_series.iloc[-1])
    except Exception:
        sma200 = None

    # ------------------------------------------------------------------
    # MACD — Moving Average Convergence Divergence
    # ------------------------------------------------------------------
    # MACD = 12-period EMA - 26-period EMA
    # Signal line = 9-period EMA of MACD
    #
    # Interpretation:
    #   MACD line crosses ABOVE signal line → Bullish crossover (buy signal)
    #   MACD line crosses BELOW signal line → Bearish crossover (sell signal)
    #
    # The histogram (MACD - Signal) shows momentum acceleration/deceleration.
    # ------------------------------------------------------------------
    try:
        macd_obj = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd_obj.macd().iloc[-1]
        macd_signal = macd_obj.macd_signal().iloc[-1]
        macd_bullish = bool(macd_line > macd_signal)
    except Exception:
        macd_bullish = None

    # ------------------------------------------------------------------
    # Volume Spike — Abnormal trading activity
    # ------------------------------------------------------------------
    # A volume spike suggests heightened interest (news, earnings, breakouts).
    # We flag days where volume is > 1.5x the 20-day average.
    #
    # Interpretation:
    #   Volume spike + price up   → Strong buying conviction (breakout)
    #   Volume spike + price down → Strong selling (distribution)
    #   Low volume + price move   → Weak conviction, likely reversal
    # ------------------------------------------------------------------
    try:
        avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
        latest_volume = float(volume.iloc[-1])
        volume_spike = bool(latest_volume > 1.5 * avg_volume_20) if avg_volume_20 > 0 else False
    except Exception:
        volume_spike = False

    # ------------------------------------------------------------------
    # 52-Week High/Low Percentage
    # ------------------------------------------------------------------
    # Shows how far the current price is from its 52-week extremes.
    # Useful for identifying stocks near support (52W low) or resistance (52W high).
    #
    # Interpretation:
    #   Near 52W high (0-5%) → Strong momentum, may face resistance
    #   Near 52W low (0-10%) → Potential bottom-fishing opportunity
    #   Middle range          → No extreme positioning
    # ------------------------------------------------------------------
    try:
        high_52w = float(close.max())
        low_52w = float(close.min())
        range_52w = high_52w - low_52w

        if range_52w > 0:
            pct_from_52w_high = ((high_52w - latest_price) / range_52w) * 100
            pct_from_52w_low = ((latest_price - low_52w) / range_52w) * 100
        else:
            pct_from_52w_high = None
            pct_from_52w_low = None
    except Exception:
        pct_from_52w_high = None
        pct_from_52w_low = None

    return {
        "price": round(latest_price, 2),
        "rsi": round(rsi, 2) if rsi is not None else None,
        "sma50": round(sma50, 2) if sma50 is not None else None,
        "sma200": round(sma200, 2) if sma200 is not None else None,
        "macd_bullish": macd_bullish,
        "volume_spike": volume_spike,
        "pct_from_52w_high": round(pct_from_52w_high, 2) if pct_from_52w_high is not None else None,
        "pct_from_52w_low": round(pct_from_52w_low, 2) if pct_from_52w_low is not None else None,
    }


def calculate_all_indicators(stock_data: dict[str, pd.DataFrame]) -> tuple[list[dict], list[str]]:
    """
    Calculate indicators for all stocks in the dataset.

    Args:
        stock_data: Dict mapping ticker -> OHLCV DataFrame

    Returns:
        Tuple of (list of indicator dicts, list of failed tickers)
    """
    results: list[dict] = []
    failed: list[str] = []

    for ticker, df in stock_data.items():
        indicators = calculate_indicators(df)
        if indicators:
            indicators["ticker"] = ticker
            results.append(indicators)
        else:
            failed.append(ticker)

    return results, failed


if __name__ == "__main__":
    from data import fetch_stock_data

    print("Testing indicators for RELIANCE...")
    df = fetch_stock_data("RELIANCE", period_days=365)
    if df is not None:
        ind = calculate_indicators(df)
        for k, v in ind.items():
            print(f"  {k}: {v}")
    else:
        print("Failed to fetch data")
