import os
import re
import json
import yfinance as yf
from datetime import datetime, timedelta

def audit_trades(picks):
    results = []
    for pick in picks:
        ticker = pick["Ticker"]
        try:
            data = yf.Ticker(ticker).history(period="1mo")
            if data.empty: continue
            
            entry = pick.get("Entry", data['Close'].iloc[0])
            tp = pick.get("TP", entry * 1.15)
            sl = pick.get("SL", entry * 0.95)
            
            high = data['High'].max()
            low = data['Low'].min()
            current = data['Close'].iloc[-1]
            
            status = "ACTIVE"
            current_pl = ((current - entry) / entry) * 100
            notes = "Maintaining above support."
            
            if low <= sl:
                status = "STOPPED OUT"
                current_pl = ((sl - entry) / entry) * 100
                notes = f"Hit Hard Stop at {sl:.2f}."
            elif high >= tp:
                status = "TARGET HIT (TRAILING)"
                potential_trailing = high * 0.95
                trailing_sl = max(entry, potential_trailing)
                if current <= trailing_sl:
                    status = "CLOSED (TRAILING SL)"
                    current_pl = ((trailing_sl - entry) / entry) * 100
                    notes = f"Trailing Stop hit at {trailing_sl:.2f}."
                else:
                    notes = f"Target hit! Trailing active at {trailing_sl:.2f}."

            results.append({
                "Trade Date": pick["ReportDate"],
                "Ticker": ticker,
                "Status": status,
                "Current P/L": f"{current_pl:.2f}%",
                "Notes": notes
            })
        except:
            continue
    return results

def save_json_data(new_picks, audit_results):
    data = {
        "latest_picks": new_picks,
        "audit": audit_results,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    with open("audit_results.json", "w") as f:
        json.dump(data, f)

if __name__ == "__main__":
    # Mocking historical data for the audit ledger
    historical_picks = [
        {"Ticker": "NVDA", "ReportDate": "2026-04-25", "Entry": 180, "TP": 210, "SL": 170},
        {"Ticker": "AAPL", "ReportDate": "2026-04-27", "Entry": 260, "TP": 300, "SL": 250}
    ]
    audit_results = audit_trades(historical_picks)
    
    # Mocking new picks that Agent 3 would select
    new_picks = [
        {
            "Ticker": "TSLA", "Entry": 180, "TP": 210, "SL": 170, 
            "Size": "5%", "Horizon": "2-4 Weeks", 
            "Reason": "Breaking out of falling wedge on daily chart with high relative strength."
        },
        {
            "Ticker": "AMD", "Entry": 150, "TP": 180, "SL": 140, 
            "Size": "3%", "Horizon": "1-2 Weeks", 
            "Reason": "Sector momentum in semiconductors following positive earnings from peers."
        },
        {
            "Ticker": "MSFT", "Entry": 400, "TP": 460, "SL": 380, 
            "Size": "4%", "Horizon": "1 Month", 
            "Reason": "Consolidating at all-time highs with strong institutional buying on dips."
        }
    ]
    
    save_json_data(new_picks, audit_results)
    
    # Generate the MD report as well
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    with open(f"{date_str}_EST.md", "w") as f:
        f.write(f"# Daily Stock Report - {date_str}\n\n")
        f.write("## Performance Audit\n| Date | Ticker | Status | P/L | Notes |\n|---|---|---|---|---|\n")
        for r in audit_results:
            f.write(f"| {r['Trade Date']} | {r['Ticker']} | {r['Status']} | {r['Current P/L']} | {r['Notes']} |\n")
