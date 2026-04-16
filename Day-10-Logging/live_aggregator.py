import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.live import StockDataStream
from alpaca.data.models import Trade
from alpaca.data.enums import DataFeed
import logging

# Set up the production logger
logging.basicConfig(
    filename='engine.log',       # The file where data will be permanently saved
    level=logging.INFO,          # The severity level to record
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load hidden API keys
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise ValueError("CRITICAL ERROR: API keys not found in .env file.")

class TickAggregator:
    def __init__(self, symbol: str, interval_minutes: int = 1):
        self.symbol = symbol
        self.interval_minutes = interval_minutes
        self.current_candle = None
        
        # New VWAP State Variables
        self.cumulative_volume = 0
        self.cumulative_typical_price_volume = 0

    def process_tick(self, trade: Trade):
        # Truncate the trade's exact timestamp down to the nearest minute boundary
        tick_time = trade.timestamp.replace(second=0, microsecond=0)
        print("Ding")
        # 1. Start the very first candle
        if self.current_candle is None:
            self._start_new_candle(tick_time, trade)
            return

        # 2. Check if the tick belongs to a NEW time interval
        # If the tick's minute is greater than our current candle's minute, the candle is closed.
        if tick_time > self.current_candle['time']:
            self._close_and_print_candle()
            self._start_new_candle(tick_time, trade)
        
        # 3. Otherwise, the tick belongs to the CURRENT candle. Update the state.
        else:
            self.current_candle['high'] = max(self.current_candle['high'], trade.price)
            self.current_candle['low'] = min(self.current_candle['low'], trade.price)
            self.current_candle['close'] = trade.price
            self.current_candle['volume'] += trade.size

        # --- VWAP Calculation ---
        # Typical Price is the average of the High, Low, and Close of the trade
        typical_price = (trade.price + trade.price + trade.price) / 3 # Since it's a single tick, H=L=C=Price
        
        self.cumulative_volume += trade.size
        self.cumulative_typical_price_volume += (typical_price * trade.size)
    
    def _start_new_candle(self, start_time: datetime, trade: Trade):
        self.current_candle = {
            'time': start_time,
            'open': trade.price,
            'high': trade.price,
            'low': trade.price,
            'close': trade.price,
            'volume': trade.size
        }

    def _close_and_print_candle(self):
        c = self.current_candle
        
        # Calculate current VWAP
        current_vwap = self.cumulative_typical_price_volume / self.cumulative_volume if self.cumulative_volume > 0 else 0
        
        # time_str = c['time'].strftime('%H:%M')
        logging.info(f"{self.symbol} | C: ${c['close']:.2f} | Vol: {c['volume']} | VWAP: ${current_vwap:.2f}")

  # Initialize our stateful aggregator for 1-minute SPY candles
spy_aggregator = TickAggregator(symbol="SPY", interval_minutes=1)

# The async callback that fires every time a trade happens
async def trade_callback(trade: Trade):
    # Pass the raw tick into our aggregator engine
    spy_aggregator.process_tick(trade)

# Boot up the WebSocket
stream = StockDataStream(API_KEY, SECRET_KEY, feed=DataFeed.IEX)
stream.subscribe_trades(trade_callback, "SPY")

print("Engine Online. Ingesting raw ticks and aggregating into 1-minute OHLCV candles...")
print("Note: The first candle will print exactly when the clock rolls over to the next minute.")

stream.run()