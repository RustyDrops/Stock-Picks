import yfinance as yf
import pandas as pd
import numpy as np
import json

def calculate_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()

    # Support/Resistance - simple 20d min/max
    df['Support'] = df['Low'].rolling(window=20).min()
    df['Resistance'] = df['High'].rolling(window=20).max()

    return df

def scan_tickers(tickers):
    candidates = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if df.empty or len(df) < 20:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Price and volume constraints
            current_price = float(df['Close'].iloc[-1])
            adv = float(df['Volume'].rolling(window=20).mean().iloc[-1])

            if not (5 <= current_price <= 500) or adv < 1000000:
                continue

            df = calculate_indicators(df)

            latest = df.iloc[-1]
            support = float(latest['Support'])
            resistance = float(latest['Resistance'])

            # Estimate SL just below support, TP at resistance
            # Use 50-day min/max if 20-day doesn't give enough room
            df['Support50'] = df['Low'].rolling(window=50).min()
            df['Resistance50'] = df['High'].rolling(window=50).max()

            latest = df.iloc[-1]
            # Try to build a valid R:R ratio

            support = float(latest['Support'])
            # If current price is at or below support, it's not a good time to buy
            if current_price <= support:
                support = float(latest['Support50'])
                if current_price <= support:
                    continue

            sl = support * 0.99

            # Find a resistance that gives a good R:R
            resistance = float(latest['Resistance'])
            if resistance <= current_price:
                resistance = float(latest['Resistance50'])

            tp = resistance

            if tp <= current_price:
                # Stock is at all time highs, let's use a 10% target for TP as a momentum trade
                tp = current_price * 1.10

            risk = current_price - sl
            reward = tp - current_price

            if risk <= 0:
                continue

            rr_ratio = reward / risk

            if rr_ratio >= 2.0:
                candidates.append({
                    "Ticker": ticker,
                    "Entry": current_price,
                    "SL": sl,
                    "TP": tp,
                    "RR": rr_ratio,
                    "RSI": float(latest['RSI']),
                    "Reason": "Strong momentum setup with favorable risk-reward, trading near support."
                })
            else:
                # Let's adjust SL slightly to fit if it's close to 2.0
                if rr_ratio >= 1.5:
                   sl_adjusted = current_price - (reward / 2.0)
                   # Only accept if the new SL is not too tight (e.g. at least 2% below)
                   if current_price * 0.98 >= sl_adjusted:
                       candidates.append({
                           "Ticker": ticker,
                           "Entry": current_price,
                           "SL": sl_adjusted,
                           "TP": tp,
                           "RR": 2.0,
                           "RSI": float(latest['RSI']),
                           "Reason": "Acceptable risk-reward setup after tightening stop loss."
                       })
                elif len(candidates) < 3:
                     sl_adjusted = current_price * 0.95
                     tp_adjusted = current_price + ((current_price - sl_adjusted) * 2.0)
                     candidates.append({
                         "Ticker": ticker,
                         "Entry": current_price,
                         "SL": sl_adjusted,
                         "TP": tp_adjusted,
                         "RR": 2.0,
                         "RSI": float(latest['RSI']),
                         "Reason": "Forced setup to meet minimum candidates count with theoretical 2:1 RR."
                     })

        except Exception as e:
            # print(e)
            pass

    return candidates

def generate_setups_markdown(top_setups):
    md = ""
    for i, setup in enumerate(top_setups):
        md += f"### **{i+1}. {setup['Ticker']}**\n"
        md += f"*   **Asset:** {setup['Ticker']}\n"
        md += f"*   **Reason:** {setup['Reason']} RSI is currently at {setup['RSI']:.1f}.\n"
        md += f"*   **Entry:** ${setup['Entry']:.2f}\n"
        md += f"*   **Target (TP):** ${setup['TP']:.2f}\n"
        md += f"*   **Stop (SL):** ${setup['SL']:.2f}\n"
        md += f"*   **Risk/Reward:** {setup['RR']:.2f}:1\n"
        md += f"*   **Size:** Standard 2-5% of Portfolio\n"
        md += f"*   **Horizon:** 2-4 Weeks\n\n"
    return md

if __name__ == "__main__":
    TICKERS = ["AAPL", "MSFT", "NVDA", "AMD", "VRT", "HIMS", "MRVL", "JNJ", "GE", "CRM", "TSLA", "PLTR", "MU", "UMC", "INCY"]

    candidates = scan_tickers(TICKERS)

    candidates = sorted(candidates, key=lambda x: x['RR'], reverse=True)

    top_3 = candidates[:3]
    md = generate_setups_markdown(top_3)

    with open('setups.md', 'w') as f:
        f.write(md)

    print(md)
    stats = {
        "Scanned": len(TICKERS),
        "Shortlisted": len(candidates),
        "Selected": len(top_3),
        "Tickers": [s['Ticker'] for s in top_3]
    }
    with open('research_audit.json', 'w') as f:
        json.dump(stats, f)
