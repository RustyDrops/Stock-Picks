import yfinance as yf
import pandas as pd
import glob
import re
import json
import os
from datetime import datetime

def parse_markdown_files():
    files = glob.glob('2026-*.md')
    trade_data = []

    for file in files:
        # Extract trade date from filename (e.g. 2026-04-27)
        match = re.search(r'(\d{4}-\d{2}-\d{2})', file)
        if not match:
            continue
        trade_date = match.group(1)

        # Calculate days ago
        trade_dt = datetime.strptime(trade_date, '%Y-%m-%d')
        now_dt = datetime.now()
        days_ago = (now_dt - trade_dt).days

        # The prompt says approximately 7, 14, 21, and 28 days ago.
        # Given this is just a short timeframe we can include all found ones if they are in the past
        if days_ago < 0:
            continue

        with open(file, 'r') as f:
            content = f.read()

        # Regex to find setups block and extract individual setups
        setups_block = re.search(r'## 2\. Top 3 Setups(.*?)(?:## 3\.|---)', content, re.DOTALL)
        if not setups_block:
            continue

        text = setups_block.group(1)
        parts = re.split(r'\n### |\n\*\*\d\.', text)

        for part in parts:
            if not part.strip(): continue

            ticker = None
            ticker_match = re.search(r'\b([A-Z]{1,5})\b\s*\(|\(([A-Z]{1,5})\)', part)
            if ticker_match:
                ticker = ticker_match.group(1) or ticker_match.group(2)
            else:
                asset_match = re.search(r'\*\*Asset:\*\*.*?(?:NYSE|NASDAQ):\s*([A-Z]+)', part)
                if asset_match:
                    ticker = asset_match.group(1)
                else:
                    setup_match = re.search(r'Setup \d+: ([A-Z]+)', part)
                    if setup_match:
                        ticker = setup_match.group(1)

            if not ticker: continue

            entry_match = re.search(r'\*\*Entry.*?\*\*[^$]*\$([0-9.]+)', part, re.IGNORECASE)
            tp_match = re.search(r'\*\*Target.*?\*\*[^$]*\$([0-9.]+)', part, re.IGNORECASE)
            sl_match = re.search(r'\*\*Stop.*?\*\*[^$]*\$([0-9.]+)', part, re.IGNORECASE)

            if entry_match and tp_match and sl_match:
                entry = float(entry_match.group(1))
                tp = float(tp_match.group(1))
                sl = float(sl_match.group(1))
                trade_data.append({"Ticker": ticker, "Entry": entry, "TP": tp, "SL": sl, "ReportDate": trade_date})

    return trade_data

def fetch_prices(trade_data):
    if not trade_data:
        return []

    results = []
    # yfinance cache
    history = {}

    end_date = (datetime.now() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

    for trade in trade_data:
        ticker = trade['Ticker']
        start_date = trade['ReportDate']

        try:
            # Optimize by fetching once per ticker from earliest start_date
            # Here we just fetch per trade for simplicity but handle MultiIndex
            df = yf.download([ticker], start=start_date, end=end_date, progress=False)
            if df.empty:
                continue

            # Flatten columns if MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                high = df['High'][ticker].max()
                low = df['Low'][ticker].min()
                current = df['Close'][ticker].iloc[-1]
            else:
                high = df['High'].max()
                low = df['Low'].min()
                current = df['Close'].iloc[-1]

            results.append({
                "Ticker": ticker,
                "Entry": trade['Entry'],
                "SL": trade['SL'],
                "TP": trade['TP'],
                "ReportDate": trade['ReportDate'],
                "High": float(high),
                "Low": float(low),
                "Current": float(current)
            })
        except Exception as e:
            # print(f"Error fetching data for {ticker}: {e}")
            pass

    return results

if __name__ == "__main__":
    trades = parse_markdown_files()
    if trades:
        # We sort them by date just to be nice
        trades = sorted(trades, key=lambda x: x['ReportDate'])
        results = fetch_prices(trades)
        print(json.dumps(results, indent=2))
    else:
        print("[]")
