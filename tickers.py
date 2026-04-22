"""
Nifty 50 constituent tickers for NSE (National Stock Exchange of India).

jugaad-data uses pure NSE symbols without any suffix.
This list is hardcoded to avoid an API call to fetch constituents.

Note: Constituents change occasionally. Check NSE website for latest:
https://www.nseindia.com/products-services/indices-nifty50
"""

NIFTY50_TICKERS = [
    "RELIANCE",   # Reliance Industries
    "TCS",        # Tata Consultancy Services
    "HDFCBANK",   # HDFC Bank
    "INFY",       # Infosys
    "ICICIBANK",  # ICICI Bank
    "HINDUNILVR", # Hindustan Unilever
    "ITC",        # ITC Limited
    "SBIN",       # State Bank of India
    "BHARTIARTL", # Bharti Airtel
    "KOTAKBANK",  # Kotak Mahindra Bank
    "LT",         # Larsen & Toubro
    "AXISBANK",   # Axis Bank
    "ASIANPAINT", # Asian Paints
    "MARUTI",     # Maruti Suzuki
    "TITAN",      # Titan Company
    "BAJFINANCE", # Bajaj Finance
    "WIPRO",      # Wipro
    "NESTLEIND",  # Nestle India
    "ULTRACEMCO", # UltraTech Cement
    "POWERGRID",  # Power Grid Corp
    "NTPC",       # NTPC Limited
    "SUNPHARMA",  # Sun Pharmaceutical
    "M&M",        # Mahindra & Mahindra
    "TECHM",      # Tech Mahindra
    "HCLTECH",    # HCL Technologies
    "TATASTEEL",  # Tata Steel
    "INDUSINDBK", # IndusInd Bank
    "GRASIM",     # Grasim Industries
    "JSWSTEEL",   # JSW Steel
    "ADANIENT",   # Adani Enterprises
    "ADANIPORTS", # Adani Ports
    "CIPLA",      # Cipla
    "DRREDDY",    # Dr. Reddy's Laboratories
    "DIVISLAB",   # Divi's Laboratories
    "EICHERMOT",  # Eicher Motors
    "HEROMOTOCO", # Hero MotoCorp
    "BAJAJFINSV", # Bajaj Finserv
    "BPCL",       # Bharat Petroleum
    "COALINDIA",  # Coal India
    "HINDALCO",   # Hindalco Industries
    "APOLLOHOSP", # Apollo Hospitals
    "BRITANNIA",  # Britannia Industries
    "TATACONSUM", # Tata Consumer Products
    "SBILIFE",    # SBI Life Insurance
    "HDFCLIFE",   # HDFC Life Insurance
    "ONGC",       # Oil & Natural Gas Corp
    "UPL",        # UPL Limited
    "TATAMOTORS", # Tata Motors
    "SHRIRAMFIN", # Shriram Finance
    "BEL",        # Bharat Electronics
]

# Sanity check: ensure we have exactly 50 tickers
assert len(NIFTY50_TICKERS) == 50, f"Expected 50 tickers, got {len(NIFTY50_TICKERS)}"
