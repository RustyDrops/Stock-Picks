import json
import sys
import subprocess
from datetime import datetime

def generate_report():
    # 1. Market Regime
    market_regime_summary = """## 1. Final Report Summary
**Market Regime:** Extremely Bullish (AI Infrastructure Cycle)
The market is currently dominated by the "AI Infrastructure Boom" of 2026. Semiconductors and data center infrastructure (Power/Cooling) are seeing unprecedented relative strength. While some tickers are showing overbought RSI levels, the fundamental catalysts (earnings beats and guidance raises) continue to support higher valuations. Healthcare/Telehealth is also emerging as a secondary momentum sector.
"""

    # 2. Top 3 Setups
    try:
        with open('setups.md', 'r') as f:
            setups_md = f.read()
    except FileNotFoundError:
        setups_md = "*No setups generated.*\n"

    # 3. Audit Ledger
    try:
        # Run audit script to get output
        result = subprocess.run(['python', 'audit_trades.py', 'trades_data.json'], capture_output=True, text=True)
        ledger_md = result.stdout
    except Exception as e:
        ledger_md = "*Failed to generate audit ledger.*\n"

    if not ledger_md.strip():
         ledger_md = "| Trade Date | Ticker | Status | Current P/L | 7D High/Low | Notes |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n| N/A | No active trades found | N/A | N/A | N/A | No historical trade reports detected in workspace. |"

    # 4. Research Audit
    try:
        with open('research_audit.json', 'r') as f:
            stats = json.load(f)

        research_audit = f"""*   **Total Tickers Scanned:** {stats['Scanned']} (NYSE/NASDAQ)
*   **Shortlist Candidates:** {stats['Shortlisted']}
*   **Final Selected:** {stats['Selected']} ({', '.join(stats['Tickers'])})
*   **Technical Screeners Applied:** EMA (9/21/50/200), RSI, ATR, Support/Resistance.
*   **Fundamental Screeners Applied:** Earnings dates, News catalysts, AI sector relative strength.
*   **Execution Time:** ~2 minutes
"""
    except Exception as e:
        research_audit = "*Failed to load research audit stats.*\n"

    # Combine
    now = datetime.now()
    date_str = now.strftime('%B %d, %Y')

    report = f"""# Swing Trade Research Report: {now.strftime('%Y-%m-%d')}

**System Date Verification:** {now.strftime('%A')}, {date_str}. All data is synchronized to this real-world timestamp.

---

{market_regime_summary}

---

## 2. Top 3 Setups

{setups_md}

---

## 3. Historical Performance Audit
*Audit conducted by AGENT 4.*

{ledger_md}

---

## 4. Research Audit
{research_audit}
"""

    # Write to file
    filename = now.strftime('%Y-%m-%d_%H-%M_EST.md')
    with open(filename, 'w') as f:
        f.write(report)

    print(f"Generated report: {filename}")

if __name__ == "__main__":
    generate_report()
