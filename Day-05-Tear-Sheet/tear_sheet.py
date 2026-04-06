import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import yfinance as yf

# --- Helper functions for the example ---
# These are copied from other files to make this script self-contained and runnable.

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

def rsi_strategy_returns(price_data: pd.DataFrame, rsi_window: int = 14, oversold: int = 30, overbought: int = 70) -> pd.Series:
    """
    Calculates the daily returns of a simple RSI strategy.
    This is a self-contained function representing a trading strategy.
    """
    data = price_data.copy()
    close_prices = data['Close'].squeeze()
    data['rsi'] = calculate_rsi(close_prices, window=rsi_window)
    data['buy_signal'] = ((data['rsi'].shift(1) < oversold) & (data['rsi'] >= oversold))
    data['sell_signal'] = ((data['rsi'].shift(1) > overbought) & (data['rsi'] <= overbought))
    signal = pd.Series(np.nan, index=close_prices.index)
    signal.loc[data['buy_signal']] = 1
    signal.loc[data['sell_signal']] = 0
    data['position'] = signal.ffill().fillna(0)
    data['daily_return'] = close_prices.pct_change()
    strategy_returns = data['daily_return'] * data['position'].shift(1)
    return strategy_returns.fillna(0)


# --- Main Function for the Tear Sheet ---

def generate_tear_sheet(strategy_returns: pd.Series):
    """
    Generates a tear sheet with core institutional risk metrics and plots for a given strategy's returns.

    The function calculates and prints:
    1. Total Cumulative Return
    2. Annualized Volatility
    3. Annualized Sharpe Ratio (assuming a 0% risk-free rate)
    4. Maximum Drawdown

    It also generates a 2-panel chart:
    - Top Panel: Cumulative Equity Curve
    - Bottom Panel: Underwater Chart (Drawdown over time)

    Args:
        strategy_returns (pd.Series): A pandas Series of daily percentage returns.
    """
    # --- 1. Data Preparation ---
    # Ensure we are working with a clean series of returns, filling NaNs
    returns = strategy_returns.fillna(0)

    # --- 2. Calculate Core Metrics ---

    # Calculate the equity curve (cumulative growth of $1)
    equity_curve = (1 + returns).cumprod()

    # Total Cumulative Return
    total_return = equity_curve.iloc[-1] - 1

    # Annualized Volatility
    # The standard deviation of daily returns, scaled by the square root of trading days in a year (252)
    annualized_volatility = returns.std() * np.sqrt(252)

    # Annualized Sharpe Ratio
    # (Mean daily return / Std Dev of daily return) * sqrt(252)
    # This assumes a risk-free rate of 0.
    # We add a small epsilon to the denominator to avoid division by zero if volatility is zero.
    sharpe_ratio = (returns.mean() / (returns.std() + 1e-8)) * np.sqrt(252)

    # Maximum Drawdown
    # First, calculate the running maximum of the equity curve
    running_max = equity_curve.cummax()
    # Then, calculate the drawdown as the percentage drop from the running max
    drawdown = (equity_curve - running_max) / running_max
    # The maximum drawdown is the minimum (most negative) value in the drawdown series
    max_drawdown = drawdown.min()

    # --- 3. Print Metrics ---
    print("\n--- Strategy Performance Metrics ---")
    print(f"Total Cumulative Return: {total_return:.2%}")
    print(f"Annualized Volatility:   {annualized_volatility:.2%}")
    print(f"Annualized Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown:        {max_drawdown:.2%}")
    print("------------------------------------\n")

    # --- 4. Generate Plots ---
    print("Generating performance charts...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    fig.suptitle('Strategy Performance Analysis', fontsize=16)

    # Top Panel: Cumulative Equity Curve
    ax1.plot(equity_curve.index, equity_curve, color='blue', linewidth=2)
    ax1.set_title('Cumulative Equity Curve')
    ax1.set_ylabel('Growth of $1')
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    # Use a logarithmic scale for better visualization of long-term growth
    ax1.set_yscale('log')
    # Format y-axis to show normal numbers instead of scientific notation
    ax1.yaxis.set_major_formatter(mticker.ScalarFormatter())
    ax1.yaxis.get_major_formatter().set_scientific(False)
    ax1.yaxis.get_major_formatter().set_useOffset(False)

    # Bottom Panel: Underwater Chart (Drawdown)
    ax2.plot(drawdown.index, drawdown, color='red', linewidth=1)
    ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
    ax2.set_title('Underwater Chart (Drawdown)')
    ax2.set_ylabel('Drawdown')
    ax2.set_xlabel('Date')
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
    # Format y-axis as percentages
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
    plt.show()


if __name__ == "__main__":
    # --- Example Usage ---
    # This block demonstrates how to use the generate_tear_sheet function.
    # It generates returns from a simple RSI strategy and then analyzes them.

    # 1. Define parameters for the example strategy
    TICKER = 'MSFT'
    START_DATE = '2018-01-01'
    END_DATE = '2023-12-31'

    # 2. Fetch price data
    print(f"Fetching data for {TICKER} to generate sample strategy returns...")
    price_data = yf.download(TICKER, start=START_DATE, end=END_DATE, progress=False)

    if price_data.empty:
        print("Could not fetch data. Exiting example.")
    else:
        # 3. Generate strategy returns
        # Here, we use the RSI strategy from another lesson as an example input.
        # The `generate_tear_sheet` function can work with ANY series of daily returns.
        print("Calculating returns for a sample RSI strategy...")
        example_returns = rsi_strategy_returns(price_data)

        # 4. Generate the tear sheet for the example returns
        generate_tear_sheet(example_returns)