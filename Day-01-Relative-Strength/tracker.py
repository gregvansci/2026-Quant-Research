import yfinance as yf

def run_tracker():
  # 1. Define the target stock and benchmark ETF
  target_tickers = ["NVDA", "SMH"]

  # 2. Download 1 month of daily data
  print(f"Fetching data for {target_tickers}...")
  data = yf.download(target_tickers, period="1mo", interval="1d", progress=False)

  # 3. Isolate the close prices
  closings = data ['Close']

  #4. Print the top 5 rows to verify our data structure
  print("\n--- Raw Closing Prices ---")
  print(closings.head())

if __name__ == "__main__":
    run_tracker()