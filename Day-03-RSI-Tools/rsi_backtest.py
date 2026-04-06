import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) using an exponential moving average.
    """
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()

    rs = avg_gain / (avg_loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def run_rsi_backtest(ticker: str, start_date: str, end_date: str):
    """
    Runs a backtest of a simple RSI strategy and plots the results.
    """
    # 1. Fetch Data
    print(f"Fetching data for {ticker} from {start_date} to {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if data.empty:
        print(f"No data found for {ticker}. Exiting.")
        return

    # 2. Calculate RSI
    data['rsi'] = calculate_rsi(data['Close'])

    # 3. Define Strategy Thresholds
    oversold_threshold = 30
    overbought_threshold = 70

    # 4. Generate Signals
    # A "buy" signal is generated when RSI crosses ABOVE the oversold threshold
    data['buy_signal'] = ((data['rsi'].shift(1) < oversold_threshold) & 
                          (data['rsi'] >= oversold_threshold))
    
    # A "sell" signal is generated when RSI crosses BELOW the overbought threshold
    data['sell_signal'] = ((data['rsi'].shift(1) > overbought_threshold) & 
                           (data['rsi'] <= overbought_threshold))

    # 5. Simulate Strategy and Calculate Returns
    # Create a signal series: 1 for buy, 0 for sell, NaN otherwise.
    # This approach is cleaner and avoids pandas' SettingWithCopyWarning.
    signal = pd.Series(np.nan, index=data.index)
    signal.loc[data['buy_signal']] = 1
    signal.loc[data['sell_signal']] = 0

    # Forward-fill signals to create positions, then fill initial NaNs with 0.
    data['position'] = signal.ffill().fillna(0)

    # Calculate daily returns of the stock and the strategy
    data['daily_return'] = data['Close'].pct_change()
    # We shift the position by 1 day because we make the trade decision based on
    # the previous day's close and realize the return on the current day.
    data['strategy_return'] = data['daily_return'] * data['position'].shift(1)

    # 6. Calculate Performance Metrics
    # Fill NaNs with 0 before calculating cumulative product to prevent total NaN result.
    data['buy_and_hold_return'] = (1 + data['daily_return'].fillna(0)).cumprod() - 1
    data['cumulative_strategy_return'] = (1 + data['strategy_return'].fillna(0)).cumprod() - 1

    final_buy_hold = data['buy_and_hold_return'].iloc[-1]
    final_strategy_return = data['cumulative_strategy_return'].iloc[-1]

    print("\n--- Backtest Results ---")
    print(f"Period: {start_date} to {end_date}")
    print(f"Buy and Hold Return: {final_buy_hold:.2%}")
    print(f"RSI Strategy Return: {final_strategy_return:.2%}")
    print("------------------------\n")

    # 7. Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot 1: Price, Buy/Sell Signals
    ax1.plot(data.index, data['Close'], label='Close Price')
    ax1.scatter(data.index[data['buy_signal']], data['Close'][data['buy_signal']], 
                marker='^', color='g', s=150, label='Buy Signal', zorder=5)
    ax1.scatter(data.index[data['sell_signal']], data['Close'][data['sell_signal']], 
                marker='v', color='r', s=150, label='Sell Signal', zorder=5)
    ax1.set_title(f'{ticker} RSI Strategy Backtest')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.grid(True)

    # Plot 2: RSI
    ax2.plot(data.index, data['rsi'], label='RSI(14)', color='purple')
    ax2.axhline(overbought_threshold, color='r', linestyle='--', label='Overbought (70)')
    ax2.axhline(oversold_threshold, color='g', linestyle='--', label='Oversold (30)')
    ax2.set_ylabel('RSI')
    ax2.set_xlabel('Date')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # --- Parameters ---
    # You can change these to test different stocks and timeframes
    TARGET_TICKER = 'SPGI'
    START_DATE = '2021-04-01'
    END_DATE = '2026-04-01'
    # ------------------

    run_rsi_backtest(ticker=TARGET_TICKER, start_date=START_DATE, end_date=END_DATE)