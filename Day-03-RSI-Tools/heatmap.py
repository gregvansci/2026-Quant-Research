import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) using an exponential moving average.

    Args:
        data (pd.Series): A pandas Series of prices (e.g., closing prices).
        window (int): The look-back period for the RSI calculation.

    Returns:
        pd.Series: A pandas Series containing the RSI values.
    """
    delta = data.diff()

    # Separate gains (positive changes) and losses (negative changes)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate the exponential moving average of gains and losses
    # This method is closer to the original RSI calculation by Welles Wilder
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()

    # Calculate Relative Strength (RS)
    # Add a small epsilon to avg_loss to avoid division by zero
    rs = avg_gain / (avg_loss + 1e-8)

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_heatmap():
    # 1. Define a universe of stocks to analyze
    tickers = ['NVDA', 'AMD', 'INTC', 'QCOM', 'AVGO', 'MU', 'TSM', 'SMH']
    
    print(f"Fetching 6 months of daily data for {len(tickers)} tickers...")
    # 2. Download historical data
    data = yf.download(tickers, period="6mo", interval="1d", progress=False)
    close_prices = data['Close']
    
    # 3. Calculate RSI for each ticker
    print("Calculating RSI for each ticker...")
    rsi_df = close_prices.apply(calculate_rsi)
        
    # 4. Prepare data for the heatmap (last 30 days)
    # We transpose the DataFrame so tickers are on the y-axis
    heatmap_data = rsi_df.tail(30).T
    
    # 5. Generate the heatmap
    print("Generating RSI heatmap...")
    plt.figure(figsize=(20, 8))
    
    sns.heatmap(
        heatmap_data, 
        annot=True,       # Show the RSI values on the map
        fmt=".1f",        # Format annotations to one decimal place
        linewidths=.5,    # Add lines between cells
        cmap='RdYlGn',    # Red-Yellow-Green colormap is intuitive for RSI
        vmin=20,          # Anchor the color scale minimum at 20
        vmax=80           # Anchor the color scale maximum at 80
    )
    
    # 6. Customize and show the plot
    plt.title('RSI(14) Heatmap - Last 30 Trading Days', fontsize=16)
    plt.xlabel('Date')
    plt.ylabel('Ticker')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    generate_heatmap()