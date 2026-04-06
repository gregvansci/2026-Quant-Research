import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

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

    Args:
        price_data (pd.DataFrame): DataFrame containing at least 'Close' prices.
        rsi_window (int): The look-back period for the RSI calculation.
        oversold (int): The RSI level to trigger a buy signal.
        overbought (int): The RSI level to trigger a sell signal.

    Returns:
        pd.Series: A pandas Series containing the daily returns of the strategy.
    """
    data = price_data.copy()  # Avoid modifying the original DataFrame

    # Ensure we are working with a Series for close prices, not a single-column DataFrame.
    # This can happen if yfinance is called with a list of one ticker, e.g., ['AAPL'].
    close_prices = data['Close'].squeeze()

    # 1. Calculate RSI
    data['rsi'] = calculate_rsi(close_prices, window=rsi_window)

    # 2. Generate Signals (buy when crossing up through oversold, sell when crossing down through overbought)
    data['buy_signal'] = ((data['rsi'].shift(1) < oversold) & (data['rsi'] >= oversold))
    data['sell_signal'] = ((data['rsi'].shift(1) > overbought) & (data['rsi'] <= overbought))

    # 3. Simulate Positions (1 for long, 0 for flat)
    signal = pd.Series(np.nan, index=close_prices.index)
    signal.loc[data['buy_signal']] = 1
    signal.loc[data['sell_signal']] = 0
    data['position'] = signal.ffill().fillna(0)

    # 4. Calculate Strategy Returns
    data['daily_return'] = close_prices.pct_change()
    # Shift position by 1 to avoid lookahead bias (trade is based on previous day's signal)
    strategy_returns = data['daily_return'] * data['position'].shift(1)

    return strategy_returns.fillna(0)

def run_capm_analysis(strategy_ticker: str, market_ticker: str, start_date: str, end_date: str):
    """
    Performs a CAPM analysis (Alpha, Beta) on a given strategy vs. a market benchmark.
    """
    # 1. Fetch data for the asset and the market benchmark
    print(f"Fetching data for Asset: {strategy_ticker} and Market: {market_ticker}...")
    asset_data = yf.download(strategy_ticker, start=start_date, end=end_date, progress=False)
    market_data = yf.download(market_ticker, start=start_date, end=end_date, progress=False)

    if asset_data.empty or market_data.empty:
        print("Could not fetch data for one or both tickers. Exiting.")
        return

    # 2. Calculate strategy returns using the compartmentalized function
    print("Calculating strategy returns...")
    strategy_returns = rsi_strategy_returns(asset_data)

    # 3. Calculate market returns
    # Squeeze to ensure we get a Series, not a DataFrame. This handles the case where
    # yfinance is called with a list of one ticker, e.g., ['SPY'].
    market_returns = market_data['Close'].squeeze().pct_change().fillna(0)

    # 4. Align data and prepare for regression
    # Combine into a single DataFrame to align dates and handle any missing values
    analysis_df = pd.DataFrame({
        'strategy': strategy_returns,
        'market': market_returns
    }).dropna()

    # For CAPM, returns are typically excess returns (over a risk-free rate).
    # For simplicity, we assume the risk-free rate is 0.
    Y = analysis_df['strategy']
    X = analysis_df['market']

    # 5. Perform linear regression using statsmodels
    print("Performing linear regression to find Alpha and Beta...")
    X_sm = sm.add_constant(X) # Add a constant for the intercept (Alpha)
    model = sm.OLS(Y, X_sm).fit()

    # Extract Alpha and Beta from the model parameters
    alpha_daily = model.params.iloc[0]
    beta = model.params.iloc[1]
    
    # Annualize Alpha for a more standard interpretation (252 trading days in a year)
    alpha_annual = alpha_daily * 252
    r_squared = model.rsquared

    print("\n--- CAPM Analysis Results ---")
    print(f"Strategy: RSI on {strategy_ticker} | Market: {market_ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Beta (β): {beta:.4f}")
    print(f"Annualized Alpha (α): {alpha_annual:.2%}")
    print(f"R-squared: {r_squared:.4f}")
    print("-----------------------------\n")
    print("Beta (β): Measures the volatility of the strategy relative to the market.")
    print("  - β > 1: More volatile than the market.")
    print("  - β < 1: Less volatile than the market.")
    print("\nAlpha (α): Measures the excess return of the strategy over the market, given its risk (Beta).")
    print("  - α > 0: The strategy outperformed the market on a risk-adjusted basis.")
    print("  - α < 0: The strategy underperformed the market on a risk-adjusted basis.")

    # 6. Plotting the results
    # Separate points for visual clarity: active vs. inactive strategy days
    active_days = analysis_df[analysis_df['strategy'] != 0]
    inactive_days = analysis_df[analysis_df['strategy'] == 0]

    plt.figure(figsize=(12, 8))
    
    # Scatter plot of daily returns, colored by activity
    plt.scatter(inactive_days['market'], inactive_days['strategy'], color='grey', alpha=0.5, label='Inactive Days (Strategy Return = 0)')
    plt.scatter(active_days['market'], active_days['strategy'], color='blue', alpha=0.7, label='Active Days (Strategy Trading)')

    
    # Regression line (the CAPM model)
    regression_line = alpha_daily + beta * X
    plt.plot(X, regression_line, color='red', linewidth=2, 
             label=f'Regression Line (β={beta:.2f})')
    
    plt.title(f'CAPM Analysis: {strategy_ticker} RSI Strategy vs. {market_ticker}')
    plt.xlabel(f'{market_ticker} Daily Returns (Market)')
    plt.ylabel(f'{strategy_ticker} RSI Strategy Daily Returns')
    plt.axhline(0, color='grey', linestyle='--')
    plt.axvline(0, color='grey', linestyle='--')
    plt.legend()
    plt.grid(True)
    
    # Add a text box with the key stats
    stats_text = (
        f"Annualized Alpha: {alpha_annual:.2%}\n"
        f"Beta: {beta:.4f}\n"
        f"R-squared: {r_squared:.4f}"
    )
    plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes,
             fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
             
    plt.show()


if __name__ == "__main__":
    # --- Parameters ---
    # You can change these to test different stocks, benchmarks, and timeframes
    STRATEGY_TICKER = 'AAPL'
    MARKET_TICKER = 'SPY' # S&P 500 ETF as the market benchmark
    START_DATE = '2020-01-01'
    END_DATE = '2023-12-31'
    # ------------------

    run_capm_analysis(
        strategy_ticker=STRATEGY_TICKER,
        market_ticker=MARKET_TICKER,
        start_date=START_DATE,
        end_date=END_DATE
    )