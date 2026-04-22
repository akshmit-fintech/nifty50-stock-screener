# Nifty 50 Stock Screener

A production-ready Streamlit web app that screens all **Nifty 50** stocks (National Stock Exchange of India) using technical indicators — no API keys, no rate limits.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.56-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What It Does

This app fetches historical stock data directly from **NSE India** and runs technical analysis on all 50 Nifty constituents. You can:

| Feature | Description |
|---------|-------------|
| **Preset Scans** | Run 5 built-in scans: Oversold Bounce, Momentum Breakout, Near 52W Low, Golden Cross Watch, Overbought |
| **Custom Filters** | Mix your own conditions: RSI range, SMA alignment, MACD crossover, volume spike, 52-week proximity |
| **Technical Indicators** | RSI(14), SMA-50, SMA-200, MACD, Volume Spike, 52W High/Low % |
| **Interactive Charts** | Expand any stock to see a Plotly price chart with SMA overlays |
| **Export Results** | Download filtered results as CSV |
| **Dark Theme** | Terminal-inspired dark UI |

### How the Data Flows

```
tickers.py (50 symbols)
    ↓
data.py → fetches OHLCV from NSE India via jugaad-data
    ↓
indicators.py → calculates RSI, SMA, MACD, volume metrics
    ↓
screener.py → applies your filter conditions
    ↓
app.py → renders the Streamlit UI with tables & charts
```

### Tech Stack

| Component | Library |
|-----------|---------|
| Web UI | [Streamlit](https://streamlit.io) |
| Market Data | [jugaad-data](https://github.com/jugaad-py/jugaad-data) (NSE India) |
| Technical Indicators | [ta](https://github.com/bukosabino/ta) |
| Charts | [Plotly](https://plotly.com/python/) |
| Data Processing | [Pandas](https://pandas.pydata.org) |

> **Why jugaad-data instead of yfinance?**<br>
> yfinance uses Yahoo Finance as a proxy and aggressively rate-limits IPs. jugaad-data pulls directly from NSE India — no rate limits, no API keys, purpose-built for Indian stocks.

---

## Run Locally

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd nifty-screener
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the app

```bash
python -m streamlit run app.py
```

The app opens in your browser at **`http://localhost:8501`**.

> **Note:** On first run, the app fetches ~1 year of data for all 50 stocks. This takes about 30–45 seconds. After that, data is cached for 1 hour and loads instantly.

---

## Live Demo

🚀 **Try it here:** [Nifty 50 Screener on Streamlit Cloud](https://akshmit-fintech-nifty50-stock-screener.streamlit.app/)

[GitHub Repository](https://github.com/akshmit-fintech/nifty50-stock-screener)

---

## Project Structure

```
nifty-screener/
├── app.py              # Streamlit UI entry point
├── data.py             # NSE data fetching + caching
├── indicators.py       # RSI, SMA, MACD calculations
├── screener.py         # Filter logic + 5 preset scans
├── tickers.py          # Nifty 50 constituent list
├── requirements.txt    # Python dependencies
├── .gitignore          # Python gitignore template
├── .streamlit/
│   └── config.toml     # Dark theme configuration
└── README.md           # This file
```

---

## Available Scans

| Scan | Logic | Use Case |
|------|-------|----------|
| **Oversold Bounce** | RSI < 35 + Price > SMA-200 | Buy dips in long-term uptrends |
| **Momentum Breakout** | Price > SMA-50 + MACD bullish + Volume spike | Catch strong trending moves |
| **Near 52W Low** | Within 10% of 52-week low | Value / support-level entries |
| **Golden Cross Watch** | Price > SMA-50 + Price > SMA-200 | Confirmed bull market alignment |
| **Overbought** | RSI > 70 | Profit booking / pullback zones |

---

## Understanding the Indicators

| Indicator | What It Means | Signal |
|-----------|---------------|--------|
| **RSI(14)** | Momentum oscillator (0–100) | <30 = oversold (buy), >70 = overbought (sell) |
| **SMA-50** | 50-day average price | Price above = short-term uptrend |
| **SMA-200** | 200-day average price | Price above = long-term bull market |
| **MACD** | Trend-following momentum | MACD > Signal = bullish crossover |
| **Volume Spike** | Today's volume > 1.5× 20-day avg | Confirms conviction behind the move |
| **52W %** | Distance from 52-week extremes | Near 0% = at support or resistance |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `streamlit: command not found` | Use `python -m streamlit run app.py` instead |
| App shows "No stocks matched" | Relax your filters or try a different preset |
| Charts don't render | Check that `plotly` is installed: `pip install plotly` |
| Data loads slowly | First run fetches all 50 stocks. Cached for 1 hour after that. |

---

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** → select your repo
4. Set **Main file path** to `app.py`
5. Click **Deploy** 🚀

No secrets or API keys needed — all data is public.

---

## Disclaimer

This tool is for **educational and research purposes only**. Not financial advice. Always do your own due diligence before investing.

---

## License

MIT License — free to use, modify, and distribute.

Built with ❤️ using [Streamlit](https://streamlit.io), [jugaad-data](https://github.com/jugaad-py/jugaad-data), and [ta](https://github.com/bukosabino/ta).
