import pandas as pd
from dataclasses import dataclass, field

TRADE_BAR_PROPERTIES = ["time", "open", "high", "low", "close", "volume"]

DEFAULT_MARKET_DATA_ID = 55
DEFAULT_CONTRACT_ID = 44

CREATE_BID_ASK_DATA = """
CREATE TABLE IF NOT EXISTS bid_ask_data
    (
        timestamp DATETIME,
        symbol STRING,
        bid_price REAL,
        ask_price REAL,
        bid_size INTEGER,
        ask_size INTEGER
)"""

CREATE_OPEN_ORDERS = """
CREATE TABLE IF NOT EXISTS open_orders
    (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        order_id INTEGER,
        symbol STRING,
        sec_type STRING,
        exhange STRING,
        action STRING,
        order_type STRING,
        quantity INTEGER,
        status STRING
)"""

CREATE_TRADES = """
CREATE TABLE IF NOT EXISTS trades
    (
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        request_id INTEGER,
        order_id INTEGER,
        execution_id INTEGER,
        symbol STRING,
        sec_type STRING,
        currency STRING,
        quantity INTEGER,
        last_liquidity REAL
)"""

@dataclass
class Tick:
    """
    A data structure representing a single market tick, including bid and ask prices,
    their corresponding sizes, and the timestamp of the tick event.

    Attributes:
        time (int): The Unix timestamp (seconds since epoch) when the tick was recorded.
        bid_price (float): The bid price (price buyers are willing to pay) at the tick.
        ask_price (float): The ask price (price sellers are willing to accept) at the tick.
        bid_size (float): The size/volume of the bid at the tick.
        ask_size (float): The size/volume of the ask at the tick.
        timestamp_ (pd.Timestamp): A Pandas Timestamp object representing the tick time
                                   in a human-readable datetime format.
    """
    time: int
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp_: pd.Timestamp = field(init=False)

    def __post_init__(self):
        """
        Post-initialization to convert the Unix timestamp into a Pandas Timestamp
        and to ensure numerical attributes are of the correct type.
        
        - Converts `time` to `timestamp_` using Pandas for better datetime handling.
        - Ensures `bid_price`, `ask_price` are floats and `bid_size`, `ask_size` are integers.
        """
        self.timestamp_ = pd.to_datetime(self.time, unit="s")
        self.bid_price = float(self.bid_price)
        self.ask_price = float(self.ask_price)
        self.bid_size = int(self.bid_size)
        self.ask_size = int(self.ask_size)