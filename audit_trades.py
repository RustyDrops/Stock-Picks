import json
import sys

def audit_trades(json_file):
    with open(json_file, 'r') as f:
        trade_data = json.load(f)

    results = []
    for trade in trade_data:
        status = "ACTIVE"
        current_pl = ((trade['Current'] - trade['Entry']) / trade['Entry']) * 100
        notes = "Maintaining above support."
        trailing_sl = trade['SL']

        # 1. Check if previously Stopped Out
        if trade['Low'] <= trade['SL']:
            status = "STOPPED OUT"
            current_pl = ((trade['SL'] - trade['Entry']) / trade['Entry']) * 100
            notes = f"Hit Hard Stop at {trade['SL']}."

        # 2. Check if Target was Hit
        elif trade['High'] >= trade['TP']:
            status = "TARGET HIT (TRAILING)"
            # Trailing Stop Logic: 5% below High, but at least at Entry (Break Even)
            potential_trailing = trade['High'] * 0.95
            trailing_sl = max(trade['Entry'], potential_trailing)

            # Check if currently below the new Trailing SL
            if trade['Current'] <= trailing_sl:
                status = "CLOSED (TRAILING SL)"
                current_pl = ((trailing_sl - trade['Entry']) / trade['Entry']) * 100
                notes = f"Trailing Stop hit at {trailing_sl:.2f} after reaching target."
            else:
                notes = f"Target hit! Trailing Stop active at {trailing_sl:.2f}."

        results.append({
            "Trade Date": trade['ReportDate'],
            "Ticker": trade['Ticker'],
            "Status": status,
            "Current P/L": f"{round(current_pl, 2)}%",
            "7D High/Low": f"{round(trade['High'], 2)} / {round(trade['Low'], 2)}",
            "Notes": notes
        })

    return results

def generate_markdown_table(results):
    if not results:
        return "| Trade Date | Ticker | Status | Current P/L | 7D High/Low | Notes |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n| N/A | No active trades found | N/A | N/A | N/A | No historical trade reports detected in workspace. |"

    markdown = "| Trade Date | Ticker | Status | Current P/L | 7D High/Low | Notes |\n"
    markdown += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for r in results:
        markdown += f"| {r['Trade Date']} | {r['Ticker']} | {r['Status']} | {r['Current P/L']} | {r['7D High/Low']} | {r['Notes']} |\n"
    return markdown

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audit_trades.py <json_file>")
        sys.exit(1)

    results = audit_trades(sys.argv[1])
    md_table = generate_markdown_table(results)
    print(md_table)
