import os
import re
import json
import yfinance as yf
from datetime import datetime, timedelta
from analyst_service import MarketAnalyst

def audit_trades(picks):
    results = []
    for pick in picks:
        ticker = pick["Ticker"]
        try:
            # Look back from the report date to current
            report_date = datetime.strptime(pick["ReportDate"], "%Y-%m-%d")
            data = yf.Ticker(ticker).history(start=report_date)
            if data.empty: continue
            
            entry = float(pick.get("Entry", data['Close'].iloc[0]))
            tp = float(pick.get("TP", entry * 1.15))
            sl = float(pick.get("SL", entry * 0.95))
            
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
        except Exception as e:
            print(f"Error auditing {ticker}: {e}")
            continue
    return results

def save_json_data(new_picks, audit_results):
    ledger_path = "audit_results.json"
    
    # Load existing history if it exists
    history = {"latest_picks": [], "audit": [], "full_history": []}
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r") as f:
                history = json.load(f)
        except: pass

    # Update latest picks
    history["latest_picks"] = new_picks
    
    # Sync Audit Results (Update existing or add new)
    # We use Ticker + Trade Date as a unique key for the audit
    existing_audits = {f"{a['Ticker']}_{a['Trade Date']}": a for a in history.get("audit", [])}
    for result in audit_results:
        key = f"{result['Ticker']}_{result['Trade Date']}"
        existing_audits[key] = result
    
    history["audit"] = list(existing_audits.values())
    history["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(ledger_path, "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    print("--- Starting Intelligent Stock Research ---")
    
    # 1. Load historical context for the audit
    ledger_path = "audit_results.json"
    historical_picks = []
    if os.path.exists(ledger_path):
        with open(ledger_path, "r") as f:
            data = json.load(f)
            # Audit the 'latest_picks' from the previous run plus the general history
            historical_picks = data.get("latest_picks", []) + data.get("full_history", [])
            
    # If first run, use initial seed
    if not historical_picks:
        historical_picks = [
            {"Ticker": "NVDA", "ReportDate": "2026-04-25", "Entry": 180, "TP": 210, "SL": 170},
            {"Ticker": "AAPL", "ReportDate": "2026-04-27", "Entry": 260, "TP": 300, "SL": 250}
        ]
    
    audit_results = audit_trades(historical_picks)
    print(f"Audited {len(audit_results)} trades.")

    # 2. Generate Intelligent New Picks
    analyst = MarketAnalyst()
    candidates = ["TSLA", "AMD", "MSFT", "GOOGL", "META", "AMZN", "NFLX"]
    print(f"Researching candidates: {candidates}")
    raw_picks = analyst.get_new_picks(candidates)
    
    new_picks = []
    print(f"Processing {len(raw_picks)} raw picks...")
    for p in raw_picks:
        try:
            norm_p = {k.lower(): v for k, v in p.items()}
            ticker = p.get('Ticker', norm_p.get('ticker'))
            entry = float(norm_p.get('entry', 0))
            tp = float(norm_p.get('tp', 0))
            sl = float(norm_p.get('sl', 0))
            reason = norm_p.get('reason', 'N/A')
            
            if ticker is None or entry == 0: continue

            rr = round((tp - entry) / (entry - sl), 2) if (entry - sl) != 0 else 0
            
            pick_obj = {
                "Ticker": ticker,
                "Entry": entry,
                "TP": tp,
                "SL": sl,
                "RR": rr,
                "Horizon": "1-3w",
                "Reason": reason,
                "ReportDate": datetime.now().strftime("%Y-%m-%d"),
                "Size": "5%" # Default
            }
            new_picks.append(pick_obj)
            print(f"    + Added {ticker} to final report.")
        except Exception as e:
            print(f"    ! Error formatting pick: {e}")

    print(f"Final Count: Selected {len(new_picks)} picks for today.")
    save_json_data(new_picks, audit_results)
    
    # Move current latest_picks to full_history for the NEXT audit cycle
    if os.path.exists(ledger_path):
        with open(ledger_path, "r") as f:
            final_data = json.load(f)
        
        # Clean up full_history to keep only unique entries
        history_map = {f"{p['Ticker']}_{p['ReportDate']}": p for p in final_data.get("full_history", [])}
        for p in new_picks:
            history_map[f"{p['Ticker']}_{p['ReportDate']}"] = p
        
        final_data["full_history"] = list(history_map.values())
        
        with open(ledger_path, "w") as f:
            json.dump(final_data, f, indent=2)

    # 3. Generate Markdown Report
    # ... rest of script unchanged ...
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    report_path = f"{date_str}_EST.md"
    with open(report_path, "w") as f:
        f.write(f"# Intelligent Stock Report - {date_str}\n\n")
        f.write("## Performance Audit\n| Date | Ticker | Status | P/L | Notes |\n|---|---|---|---|---|\n")
        for r in audit_results:
            f.write(f"| {r['Trade Date']} | {r['Ticker']} | {r['Status']} | {r['Current P/L']} | {r['Notes']} |\n")
        
        f.write("\n## AI Selected Picks\n| Ticker | Entry | TP | SL | RR | Horizon | Reason |\n|---|---|---|---|---|---|---|\n")
        for p in new_picks:
            f.write(f"| {p['Ticker']} | {p['Entry']} | {p['TP']} | {p['SL']} | {p['RR']} | {p['Horizon']} | {p['Reason']} |\n")
    
    print(f"Report generated: {report_path}")
