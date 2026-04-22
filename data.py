"""
Data fetching module for Nifty 50 stock screener.

Uses jugaad-data to fetch historical OHLCV data directly from NSE India.
jugaad-data has built-in caching and does not have Yahoo Finance rate limits.

Columns returned by stock_df:
    DATE, SERIES, OPEN, HIGH, LOW, PREV. CLOSE, LTP, CLOSE,
    VWAP, VOLUME, VALUE, NO OF TRADES, DELIVERY QTY, DELIVERY %, SYMBOL
"""

from typing import Optional, Callable
import logging
import functools
import os
import warnings
import tempfile

# Suppress harmless numpy datetime64 timezone warning from jugaad-data
warnings.filterwarnings("ignore", message="no explicit representation of timezones available for np.datetime64")

# Fix jugaad-data cache directory to avoid conflicts on Windows AND Linux
# Use a temp directory that is guaranteed to be writable and empty on fresh deploys
_CACHE_DIR = os.path.join(tempfile.gettempdir(), "nifty_screener_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)
os.environ["JUGAAD_DATA_CACHE_DIR"] = _CACHE_DIR

from datetime import date, timedelta
import time
import pandas as pd

from tickers import NIFTY50_TICKERS

# Set up logging for failed ticker fetches
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy streamlit cache warnings when running outside streamlit
try:
    logging.getLogger("streamlit.runtime.caching.cache_data_api").setLevel(logging.ERROR)
except Exception:
    pass

# Make streamlit import optional so tests work without it installed
try:
    import streamlit as st
    _cache_decorator = st.cache_data(ttl=3600, show_spinner=False)
except ImportError:
    # No-op cache decorator when streamlit is not installed
    def _cache_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize jugaad-data column names to match yfinance-style OHLCV.
    """
    rename_map = {
        "DATE": "Date",
        "OPEN": "Open",
        "HIGH": "High",
        "LOW": "Low",
        "CLOSE": "Close",
        "VOLUME": "Volume",
        "PREV. CLOSE": "PrevClose",
        "LTP": "LTP",
        "VWAP": "VWAP",
        "VALUE": "Value",
        "NO OF TRADES": "Trades",
        "DELIVERY QTY": "DeliveryQty",
        "DELIVERY %": "DeliveryPct",
        "SYMBOL": "Symbol",
        "SERIES": "Series",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df = df.set_index("Date")

    return df


@_cache_decorator
def fetch_stock_data(ticker: str, period_days: int = 365) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data for a single NSE ticker via jugaad-data.

    Args:
        ticker: NSE ticker symbol WITHOUT suffix (e.g., "RELIANCE")
        period_days: Number of days of history. Default 365 for 200-SMA.

    Returns:
        DataFrame with columns [Open, High, Low, Close, Volume] indexed by Date,
        or None if fetch fails.
    """
    try:
        from jugaad_data.nse import stock_df
    except ImportError:
        logger.error("jugaad-data not installed. Run: pip install jugaad-data")
        return None

    to_date = date.today()
    from_date = to_date - timedelta(days=period_days)

    try:
        df = stock_df(symbol=ticker, from_date=from_date, to_date=to_date, series="EQ")

        if df is None or df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None

        df = _standardize_columns(df)

        required = ["Open", "High", "Low", "Close", "Volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.warning(f"Missing columns for {ticker}: {missing}")
            return None

        return df

    except Exception as e:
        logger.error(f"Failed to fetch {ticker}: {e}")
        return None


def fetch_all_stocks_data(
    tickers: list[str],
    period_days: int = 365,
    delay: float = 0.15,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """
    Fetch data for multiple tickers sequentially.

    Args:
        tickers: List of NSE ticker symbols (no .NS suffix)
        period_days: Number of days of history.
        delay: Seconds between requests. Default 0.15s — NSE is tolerant,
               and this keeps 50-stock fetch under ~15 seconds.
        progress_callback: Optional callback(current, total, ticker) for UI progress bars.

    Returns:
        Tuple of (dict mapping ticker -> DataFrame, list of failed tickers)
    """
    failed: list[str] = []
    results: dict[str, pd.DataFrame] = {}

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i + 1, len(tickers), ticker)

        df = fetch_stock_data(ticker, period_days)
        if df is not None:
            results[ticker] = df
        else:
            failed.append(ticker)

        if i < len(tickers) - 1:
            time.sleep(delay)

    return results, failed


if __name__ == "__main__":
    print("Testing data fetch for RELIANCE...")
    df = fetch_stock_data("RELIANCE", period_days=30)
    if df is not None:
        print(f"Fetched {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        print(df.tail(3))
    else:
        print("Failed to fetch")
