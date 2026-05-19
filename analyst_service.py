import os
import json
import re
import time
import yfinance as yf
from api.micro_agents.agent_base import MicroAgent

class MarketAnalyst:
    def __init__(self):
        # Using Flash (v2.5) for higher RPD (1,500) on free tier
        self.researcher = MicroAgent("Market Researcher", model_type="flash", version="v2.5")

    def fetch_local_metrics(self, ticker):
        """
        Fetches stock data locally on the VPS since yfinance is available here.
        """
        print(f"  - Fetching local data for {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="3mo")
            if data.empty:
                return None
            
            current_price = data['Close'].iloc[-1]
            sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
            
            # RSI Calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            return {
                "price": round(current_price, 2),
                "sma50": round(sma_50, 2),
                "rsi": round(rsi, 2),
                "trend": "BULLISH" if current_price > sma_50 else "BEARISH"
            }
        except Exception as e:
            print(f"    ! Error fetching {ticker}: {e}")
            return None

    def get_new_picks(self, candidate_tickers):
        """
        Orchestrates the research and selection process.
        """
        picks = []
        for ticker in candidate_tickers:
            metrics = self.fetch_local_metrics(ticker)
            if not metrics: 
                continue
            
            # Use Researcher agent to decide
            print(f"  - AI Reasoning for {ticker}...")
            context = f"Ticker: {ticker}\nTechnical Metrics: {json.dumps(metrics)}"
            prompt = (
                "Analyze these technical metrics. If this looks like a high-probability trade, "
                "provide a plan. If not, return 'SKIP'. "
                "If picking, return ONLY a JSON object with: "
                "{\"Ticker\": \"string\", \"Entry\": number, \"TP\": number, \"SL\": number, \"Reason\": \"string\"}"
            )
            
            try:
                raw_decision = self.researcher.run_task(prompt, context=context)
                
                if "SKIP" in raw_decision.upper():
                    print(f"    - {ticker}: AI decided to skip.")
                else:
                    match = re.search(r'\{.*\}', raw_decision, re.DOTALL)
                    if match:
                        decision = json.loads(match.group())
                        decision["Ticker"] = ticker # Ensure Ticker is explicitly set
                        picks.append(decision)
                        print(f"    + {ticker}: PICKED")
                    else:
                        print(f"    ! {ticker}: No JSON in response.")
            except Exception as e:
                print(f"    ! Error in AI reasoning for {ticker}: {e}")
            
            # 2-second delay for free tier safety
            time.sleep(2)
                
        return picks

if __name__ == "__main__":
    analyst = MarketAnalyst()
    picks = analyst.get_new_picks(["NVDA", "TSLA", "AAPL"])
    print(json.dumps(picks, indent=2))
