import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

def run_tracker():
  # 1. Define the target stock and benchmark ETF
  target_tickers = ["AMD", "SMH"]

  # 2. Download 1 year of daily data
  print(f"Fetching data for {target_tickers}...")
  data = yf.download(target_tickers, period="1y", interval="1d", progress=False)

  # 3. Isolate the close prices
  closings = data ['Close']

  # 4. Print the top 5 rows to verify our data structure
  print("\n--- Raw Closing Prices ---")
  print(closings.head())

  # 5. Normalize the two symbol prices to start at 100
  normalized_closings = (closings / closings.iloc[0]) * 100

  # 6. Calculate Relative Strength (Target / Benchmark) and set baseline to 100
  relative_strength = (normalized_closings['AMD'] / normalized_closings['SMH']) * 100

  # 7. Format and print the Relative Strength
  print("\n--- Relative Strength Ratio (AMD / SMH) ---")
  print(relative_strength.round(4))

  # 7.5 Signal Generation & Basic Backtest Metric
  # Calculate a 20-day Simple Moving Average (SMA) of the Relative Strength
  rs_sma20 = relative_strength.rolling(window=20).mean()
  
  # Define a signal: True if RS > 20-day SMA. 
  # We use .shift(1) to avoid Look-Ahead Bias (we trade the day AFTER the signal)
  long_signal = (relative_strength > rs_sma20).shift(1).fillna(False)
  
  # Calculate daily returns of the target stock
  target_daily_returns = closings['AMD'].pct_change().fillna(0)
  
  # Strategy Returns (full series for equity curve, active series for trade metrics)
  full_strategy_returns = target_daily_returns * long_signal
  active_returns = target_daily_returns[long_signal]
  
  print("\n--- Strategy vs Buy & Hold (Avg Daily Return) ---")
  print(f"Buy & Hold (All Days): {target_daily_returns.mean() * 100:.3f}%")
  print(f"RS Momentum (RS > SMA20): {active_returns.mean() * 100:.3f}%")

  # --- 'The Big Three' Strategy Metrics ---
  # 1. Max Drawdown
  cumulative_returns = (1 + full_strategy_returns).cumprod()
  buy_hold_cumulative = (1 + target_daily_returns).cumprod()
  rolling_max = cumulative_returns.cummax()
  drawdown = (cumulative_returns - rolling_max) / rolling_max
  max_drawdown = drawdown.min()

  # 2. Sharpe Ratio (Annualized, assuming 0% risk-free rate)
  sharpe_ratio = (full_strategy_returns.mean() / full_strategy_returns.std()) * np.sqrt(252)

  # 3. Win Rate vs Risk/Reward (on active trading days)
  winning_days = active_returns[active_returns > 0]
  losing_days = active_returns[active_returns < 0]
  win_rate = len(winning_days) / len(active_returns) if len(active_returns) > 0 else 0
  avg_win = winning_days.mean() if len(winning_days) > 0 else 0
  avg_loss = abs(losing_days.mean()) if len(losing_days) > 0 else 0
  risk_reward = avg_win / avg_loss if avg_loss != 0 else 0

  print("\n--- Strategy Performance Metrics ('The Big Three') ---")
  print(f"Max Drawdown: {max_drawdown * 100:.2f}%")
  print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
  print(f"Win Rate:     {win_rate * 100:.1f}%")
  print(f"Risk/Reward:  {risk_reward:.2f} (Avg Win: {avg_win*100:.2f}%, Avg Loss: {avg_loss*100:.2f}%)")

  # 8. Visualize the data to make the output useful
  print("\nGenerating charts...")
  fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

  # Top plot: Normalized Prices
  ax1.plot(normalized_closings.index, normalized_closings['AMD'], label='AMD', color='blue')
  ax1.plot(normalized_closings.index, normalized_closings['SMH'], label='SMH', color='orange')
  ax1.set_title('Normalized Performance (Baseline = 100)')
  ax1.set_ylabel('Normalized Price')
  ax1.legend()
  ax1.grid(True)

  # Middle plot: Relative Strength
  ax2.plot(relative_strength.index, relative_strength, label='RS (AMD / SMH)', color='purple')
  ax2.plot(rs_sma20.index, rs_sma20, label='20-Day RS SMA', color='green', linestyle='-.')
  ax2.axhline(100, color='red', linestyle='--', alpha=0.5, label='100 Baseline')
  ax2.set_title('Relative Strength')
  ax2.set_ylabel('RS Ratio')
  ax2.legend()
  ax2.grid(True)

  # Bottom plot: Strategy Equity Curve
  ax3.plot(cumulative_returns.index, cumulative_returns * 100, label='Strategy Equity Curve', color='teal')
  ax3.plot(buy_hold_cumulative.index, buy_hold_cumulative * 100, label='Buy & Hold AMD', color='gray', alpha=0.7)
  ax3.set_title('Simulated Strategy Performance vs Buy & Hold')
  ax3.set_ylabel('Growth (Baseline 100)')
  ax3.legend()
  ax3.grid(True)

  plt.tight_layout()
  plt.show()

if __name__ == "__main__":
    run_tracker()