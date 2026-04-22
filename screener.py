"""
Screener logic for Nifty 50 Stock Screener.

Provides preset scans and custom filter support for technical indicator-based
stock screening.
"""

from typing import Optional, Callable
import pandas as pd

from data import fetch_all_stocks_data
from indicators import calculate_all_indicators
from tickers import NIFTY50_TICKERS


# --------------------------------------------------------------------------
# Prebuilt Scan Presets
# --------------------------------------------------------------------------
# Each preset is a dict of filter conditions that get applied to the
# indicator DataFrame.
# --------------------------------------------------------------------------

SCAN_PRESETS = {
    "Oversold Bounce": {
        "description": "RSI below 35 but price still above 200-SMA. "
                       "Potential mean-reversion bounce in long-term uptrend.",
        "filters": {
            "rsi_max": 35,
            "price_above_sma200": True,
        },
    },
    "Momentum Breakout": {
        "description": "Price above 50-SMA + MACD bullish crossover + volume spike. "
                       "Strong momentum with conviction.",
        "filters": {
            "price_above_sma50": True,
            "macd_bullish": True,
            "volume_spike": True,
        },
    },
    "Near 52W Low": {
        "description": "Price within 10% of 52-week low. "
                       "Potential value / support-level entries.",
        "filters": {
            "pct_from_52w_low_max": 10,
        },
    },
    "Golden Cross Watch": {
        "description": "Price above both 50-SMA and 200-SMA. "
                       "Bullish alignment of short and long-term trends.",
        "filters": {
            "price_above_sma50": True,
            "price_above_sma200": True,
        },
    },
    "Overbought": {
        "description": "RSI above 70. Potential pullback or profit-booking zone.",
        "filters": {
            "rsi_min": 70,
        },
    },
}


def _apply_filters(
    df: pd.DataFrame,
    rsi_min: Optional[float] = None,
    rsi_max: Optional[float] = None,
    price_above_sma50: Optional[bool] = None,
    price_above_sma200: Optional[bool] = None,
    macd_bullish: Optional[bool] = None,
    volume_spike: Optional[bool] = None,
    pct_from_52w_low_max: Optional[float] = None,
) -> pd.DataFrame:
    """
    Apply filter conditions to the indicator DataFrame.

    All conditions are AND-ed together (intersection).
    Missing/None conditions are skipped.
    """
    mask = pd.Series([True] * len(df), index=df.index)

    if rsi_min is not None:
        mask &= df["rsi"] >= rsi_min

    if rsi_max is not None:
        mask &= df["rsi"] <= rsi_max

    if price_above_sma50 is not None:
        mask &= df["price"] > df["sma50"]

    if price_above_sma200 is not None:
        mask &= df["price"] > df["sma200"]

    if macd_bullish is not None:
        mask &= df["macd_bullish"] == macd_bullish

    if volume_spike is not None:
        mask &= df["volume_spike"] == volume_spike

    if pct_from_52w_low_max is not None:
        mask &= df["pct_from_52w_low"] <= pct_from_52w_low_max

    return df[mask].copy()


def run_preset_scan(preset_name: str, progress_callback: Optional[Callable] = None) -> tuple[pd.DataFrame, list[str], int]:
    """
    Run a prebuilt scan preset.

    Args:
        preset_name: Key from SCAN_PRESETS dict
        progress_callback: Optional callback(current, total, ticker) for UI progress

    Returns:
        Tuple of (filtered DataFrame, failed tickers list, total stocks scanned)
    """
    if preset_name not in SCAN_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(SCAN_PRESETS.keys())}")

    # Fetch all data (cached)
    stock_data, failed = fetch_all_stocks_data(
        NIFTY50_TICKERS,
        period_days=365,
        progress_callback=progress_callback
    )

    # Calculate indicators
    indicators_list, calc_failed = calculate_all_indicators(stock_data)
    failed.extend(calc_failed)

    if not indicators_list:
        return pd.DataFrame(), failed, 0

    df = pd.DataFrame(indicators_list)
    filters = SCAN_PRESETS[preset_name]["filters"]
    result = _apply_filters(df, **filters)

    return result, list(set(failed)), len(df)


def run_custom_screener(
    rsi_min: Optional[float] = None,
    rsi_max: Optional[float] = None,
    price_above_sma50: bool = False,
    price_above_sma200: bool = False,
    macd_bullish: bool = False,
    volume_spike: bool = False,
    pct_from_52w_low_max: Optional[float] = None,
    progress_callback: Optional[Callable] = None,
) -> tuple[pd.DataFrame, list[str], int]:
    """
    Run a custom screener with user-defined filters.

    Args:
        rsi_min: Minimum RSI value (e.g., 70 for overbought)
        rsi_max: Maximum RSI value (e.g., 35 for oversold)
        price_above_sma50: Filter for price > 50-SMA
        price_above_sma200: Filter for price > 200-SMA
        macd_bullish: Filter for MACD bullish crossover
        volume_spike: Filter for volume spike
        pct_from_52w_low_max: Max % distance from 52-week low
        progress_callback: Optional callback(current, total, ticker) for UI progress

    Returns:
        Tuple of (filtered DataFrame, failed tickers list, total stocks scanned)
    """
    # Fetch all data (cached)
    stock_data, failed = fetch_all_stocks_data(
        NIFTY50_TICKERS,
        period_days=365,
        progress_callback=progress_callback
    )

    # Calculate indicators
    indicators_list, calc_failed = calculate_all_indicators(stock_data)
    failed.extend(calc_failed)

    if not indicators_list:
        return pd.DataFrame(), failed, 0

    df = pd.DataFrame(indicators_list)
    result = _apply_filters(
        df,
        rsi_min=rsi_min,
        rsi_max=rsi_max,
        price_above_sma50=price_above_sma50 if price_above_sma50 else None,
        price_above_sma200=price_above_sma200 if price_above_sma200 else None,
        macd_bullish=macd_bullish if macd_bullish else None,
        volume_spike=volume_spike if volume_spike else None,
        pct_from_52w_low_max=pct_from_52w_low_max,
    )

    return result, list(set(failed)), len(df)


if __name__ == "__main__":
    print("Testing preset scans...")
    for preset in SCAN_PRESETS:
        result, failed, total = run_preset_scan(preset)
        print(f"\n{preset}: {len(result)}/{total} stocks matched")
        if len(result) > 0:
            print(result[["ticker", "price", "rsi"]].head(3).to_string(index=False))
