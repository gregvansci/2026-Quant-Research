import os
from dotenv import load_dotenv
from alpaca.data.live import StockDataStream
from alpaca.data.models import Trade
from alpaca.data.enums import DataFeed

# 1. Load the hidden keys from the .env file
load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# 2. Safety Check: Crash the script immediately if the keys weren't found
if not API_KEY or not SECRET_KEY:
    raise ValueError("CRITICAL ERROR: API keys not found. Check your .env file.")

# 3. Initialize the WebSocket Stream
stream = StockDataStream(API_KEY, SECRET_KEY, feed=DataFeed.IEX)

# 4. The Asynchronous Callback
# This function does not run sequentially. It sits in memory and is instantly 
# triggered by the WebSocket every time someone in the world buys or sells these stocks.
async def trade_callback(trade: Trade):
    # We extract the exact microsecond timestamp, the ticker symbol, price, and volume
    time_str = trade.timestamp.strftime('%H:%M:%S.%f')[:-3]
    print(f"[{time_str}] {trade.symbol} | Price: ${trade.price:.2f} | Size: {trade.size} shares")

# 5. Subscribe and Listen
# We are subscribing to trades for Apple and Microsoft
stream.subscribe_trades(trade_callback, "SPY", "QQQ")

print("Opening secure WebSocket to the IEX Exchange...")
print("Listening for live trades (Press Ctrl+C to kill the engine)...")

# 6. Ignite the Engine
# This traps the script in an infinite loop, keeping the connection alive forever.
stream.run()