import threading
from ibapi.wrapper import EWrapper
from ibapi.common import BarData
from typing import Dict, List, Tuple


class IBWrapper(EWrapper):
    def __init__(self):
        """
        Initialize the IBWrapper.

        This class extends the EWrapper class provided by the IB API and 
        implements custom handling for historical data, market data requests, 
        account updates, and PnL data.

        Attributes:
            nextValidOrderId (int or None):
                The next valid order ID provided by the IB API. This is used to 
                ensure unique identifiers for new orders.
            historical_data (Dict[int, List[Tuple[str, float, float, float, float, int]]]):
                A dictionary to store historical data. The keys are request IDs, 
                and the values are lists of tuples containing bar data 
                (date, open, high, low, close, volume).
            market_data (Dict[int, Dict[int, float]]):
                A dictionary to store market data. The keys are request IDs, 
                and the values are dictionaries where the keys are tick types 
                and the values are the corresponding prices.
            streaming_data (Dict[int, Tuple[int, float, float, int, int]]):
                A dictionary to store streaming tick-by-tick bid/ask data. The keys 
                are request IDs, and the values are tuples containing the tick data:
                (time, bid_price, ask_price, bid_size, ask_size).
            stream_event (threading.Event):
                An event object used to signal when new streaming data is available.
            account_values (Dict[str, Tuple[float or str, str]]):
                A dictionary to store account values. The keys are account attribute 
                names (e.g., "NetLiquidation"), and the values are tuples containing 
                the value and the currency (e.g., (500000.0, "USD")).
            positions (Dict[str, Dict[str, Any]]):
                A dictionary to store portfolio positions. The keys are contract 
                symbols (e.g., "AAPL"), and the values are dictionaries containing 
                position details, including:
                    - contract: The contract object.
                    - symbol: The symbol of the contract.
                    - position: The number of units held (positive for long, negative for short).
                    - market_price: The current market price of the position.
                    - market_value: The total market value of the position.
                    - average_cost: The average cost of the position.
                    - unrealized_pnl: The unrealized profit or loss.
                    - realized_pnl: The realized profit or loss.
            account_pnl (Dict[int, Dict[str, float]]):
                A dictionary to store account PnL (profit and loss) data. The keys 
                are request IDs, and the values are dictionaries containing:
                    - daily_pnl: The daily profit or loss.
                    - unrealized_pnl: The unrealized profit or loss.
                    - realized_pnl: The realized profit or loss.
        """
        super().__init__()
        self.nextValidOrderId = None
        self.historical_data: Dict[int, List[Tuple[str, float, float, float, float, int]]] = {}
        self.market_data: Dict[int, Dict[int, float]] = {}
        self.streaming_data = {}
        self.stream_event = threading.Event()
        self.account_values = {}
        self.positions = {}
        self.account_pnl = {}
        self.portfolio_returns = None

    def nextValidId(self, order_id: int) -> None:
        """
        Callback for receiving the next valid order ID from the Interactive Brokers API.

        Args:
            order_id (int): The next valid order ID provided by the IB API.
        """
        super().nextValidId(order_id)
        self.nextValidOrderId = order_id

    def historicalData(self, request_id: int, bar: BarData):
        """
        Callback for receiving historical data from the IB API.

        Args:
            request_id (int): The unique ID for the historical data request.
            bar (BarData): A BarData object containing historical market data 
                           for a specific time interval.

        BarData attributes:
            - date (str): The date/time of the bar in string format.
            - open (float): The opening price for the interval.
            - high (float): The highest price for the interval.
            - low (float): The lowest price for the interval.
            - close (float): The closing price for the interval.
            - volume (int): The trading volume for the interval.

        Updates:
            Appends the received bar data as a tuple (date, open, high, low, close, volume) 
            to the list associated with the request_id in `historical_data`.
        """
        bar_data = (
            bar.date,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
        )
        if request_id not in self.historical_data:
            self.historical_data[request_id] = []
        self.historical_data[request_id].append(bar_data)

    def tickPrice(self, request_id: int, tick_type: int, price: float, attrib):
        """
        Callback for receiving market data (tick price) from the IB API.

        Args:
            request_id (int): The unique ID for the market data request.
            tick_type (int): The type of tick data (e.g., last price, bid, ask).
            price (float): The price data received.
            attrib: Additional attributes for the tick (ignored here).

        Updates:
            Stores the tick price in the `market_data` dictionary. The dictionary
            is organized such that `market_data[request_id][tick_type]` gives the 
            price for the specific tick type.
        """
        if request_id not in self.market_data:
            self.market_data[request_id] = {}
        self.market_data[request_id][tick_type] = float(price)

    def tickByTickAllLast(self, request_id: int, tick_type: int, time: int, price: float, size: int, attribs, exchange: str, specialConditions: str):
        """
        Callback for receiving the last trade data (Last or AllLast).

        Args:
            request_id (int): Unique ID for the tick-by-tick data request.
            tick_type (int): The type of last trade data (e.g., Last or AllLast).
            time (int): Unix timestamp for the trade.
            price (float): Last traded price.
            size (int): Trade size (volume).
            attribs: Additional attributes.
            exchange (str): The exchange where the trade occurred.
            specialConditions (str): Any special conditions for the trade.

        Updates:
            Stores the data as a tuple (time, price, size, exchange, specialConditions) in `streaming_data`.
        """
        tick_data = (time, price, size, exchange, specialConditions)
        self.streaming_data[request_id] = tick_data
        self.stream_event.set()

    def tickByTickBidAsk(self, request_id: int, time: int, bid_price: float, ask_price: float, bid_size: int, ask_size: int, attribs):
        """
        Callback for receiving bid/ask data.

        Args:
            request_id (int): Unique ID for the tick-by-tick data request.
            time (int): Unix timestamp for the bid/ask data.
            bid_price (float): Current bid price.
            ask_price (float): Current ask price.
            bid_size (int): Volume at the bid price.
            ask_size (int): Volume at the ask price.
            attribs: Additional attributes.

        Updates:
            Stores the data as a tuple (time, bid_price, ask_price, bid_size, ask_size) in `streaming_data`.
        """
        tick_data = (time, bid_price, ask_price, bid_size, ask_size)
        self.streaming_data[request_id] = tick_data
        self.stream_event.set()

    def tickByTickMidPoint(self, request_id: int, time: int, midpoint: float):
        """
        Callback for receiving midpoint data.

        Args:
            request_id (int): Unique ID for the tick-by-tick data request.
            time (int): Unix timestamp for the midpoint data.
            midpoint (float): The calculated midpoint price.

        Updates:
            Stores the data as a tuple (time, midpoint) in `streaming_data`.
        """
        tick_data = (time, midpoint)
        self.streaming_data[request_id] = tick_data
        self.stream_event.set()

    def orderStatus(
            self,
            order_id: int,
            status: str,
            filled: float,
            remaining: float,
            avg_fill_price: float,
            perm_id: int,
            parent_id: int,
            last_fill_price: float,
            client_id: int,
            why_held: str,
            mkt_cap_price: float,
        ):
            """
            Callback for receiving updates on the status of submitted orders.

            Args:
                order_id (int): The unique identifier for the order.
                status (str): The current status of the order (e.g., Submitted, Filled, Canceled).
                filled (float): The quantity of the order that has been filled.
                remaining (float): The quantity of the order that remains unfilled.
                avg_fill_price (float): The average price at which the order has been filled.
                perm_id (int): The permanent ID for the order assigned by IB.
                parent_id (int): The ID of the parent order (if any).
                last_fill_price (float): The price of the last fill for this order.
                client_id (int): The client ID associated with the order.
                why_held (str): A reason for why the order is being held (if applicable).
                mkt_cap_price (float): The market cap price.

            Purpose:
                This callback provides real-time updates on the status of an order, such as 
                when it is submitted, partially filled, completely filled, or canceled.
            
            Example Output:
                orderStatus - orderid: 1234 status: Filled filled: 100 remaining: 0 lastFillPrice: 150.25
            """
            print(
                "orderStatus - orderid:",
                order_id,
                "status:",
                status,
                "filled:",
                filled,
                "remaining:",
                remaining,
                "lastFillPrice:",
                last_fill_price,
            )

    def openOrder(self, order_id, contract, order, order_state):
        """
        Callback for receiving information about orders that are open but not yet fully executed.

        Args:
            order_id (int): The unique identifier for the order.
            contract: The financial instrument associated with the order (e.g., stock or option).
            order: The details of the order, such as action (BUY/SELL), type, and quantity.
            order_state: The current state of the order (e.g., PendingSubmit, PreSubmitted).

        Purpose:
            This callback is invoked when the API receives information about an order that 
            has been submitted but not yet fully executed. It provides details about the order
            and its current state.

        Example Output:
            openOrder id: 1234 AAPL STK @ SMART : BUY LMT 100 Submitted
        """
        
        #cursor = self.connection.cursor()
        query = """
        INSERT INTO open_orders (
            order_id, symbol, sec_type, exhange, action,
            order_type, quantity, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        # values = (
        #     order_id,
        #     contract.symbol,
        #     contract.secType,
        #     contract.exchange,
        #     order.action,
        #     order.orderType,
        #     order.totalQuantity,
        #     order_state.status,
        # )
        # cursor.execute(query, values)
        print(
            "openOrder id:",
            order_id,
            contract.symbol,
            contract.secType,
            "@",
            contract.exchange,
            ":",
            order.action,
            order.orderType,
            order.totalQuantity,
            order_state.status,
        )

    def execDetails(self, request_id: int, contract, execution):
        """
        Callback for receiving detailed information about the execution of an order.

        Args:
            request_id (int): The unique ID for the execution details request.
            contract: The financial instrument associated with the execution.
            execution: Details about the execution, including execution ID, order ID, 
                    shares executed, and last liquidity.

        Purpose:
            This callback provides granular information about the execution of an order, 
            such as the number of shares filled, execution price, and execution ID.

        Example Output:
            Order Executed:  101 AAPL STK USD 12345 1234 100 1
        """
        # cursor = self.connection.cursor()
        query = """
        INSERT INTO trades (request_id,
            symbol, sec_type, currency, execution_id,
            order_id, quantity, last_liquidity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        # values = (
        #    request_id,
        #    contract.symbol,
        #    contract.secType,
        #    contract.currency,
        #    execution.execId,
        #    execution.orderId,
        #    execution.shares,
        #    execution.lastLiquidity,
        # )
        # cursor.execute(query, values)
        print(
            "Order Executed: ",
            request_id,
            contract.symbol,
            contract.secType,
            contract.currency,
            execution.execId,
            execution.orderId,
            execution.shares,
            execution.lastLiquidity,
        )

    def updateAccountValue(self, key: str, val: str, currency: str, account: str) -> None:
        """
        Callback for processing account value updates from the Interactive Brokers API.

        Args:
            key (str): The name of the account attribute being updated (e.g., "NetLiquidation", "BuyingPower").
            val (str): The value of the account attribute as a string. It will be converted to a float if possible.
            currency (str): The currency in which the value is denominated (e.g., "USD").
            account (str): The account identifier associated with the update.

        How it works:
            - This callback is triggered by the IB API whenever an account value update is received.
            - The method attempts to convert the `val` parameter to a `float` to store numerical values in a consistent format.
            - If the conversion fails (e.g., for non-numeric values), the original string is stored instead.
            - The updated value is stored in the `self.account_values` dictionary as a tuple `(value, currency)`, keyed by the `key`.

        Updates:
            - Adds or updates the entry in the `self.account_values` dictionary for the specified `key`:
            `{key: (value, currency)}`
        """
        try:
            val_ = float(val)
        except:
            val_ = val
        self.account_values[key] = (val_, currency)

    def updatePortfolio(
        self,
        contract,
        position: float,
        market_price: float,
        market_value: float,
        average_cost: float,
        unrealized_pnl: float,
        realized_pnl: float,
        account_name: str
    ) -> None:
        """
        Callback for updating portfolio details when account updates are requested.

        Args:
            contract: The financial instrument associated with the position (an instance of `Contract`).
            position (float): The number of units held in the account (positive for long, negative for short).
            market_price (float): The current market price of the financial instrument.
            market_value (float): The current market value of the position.
            average_cost (float): The average cost per unit for the position.
            unrealized_pnl (float): The unrealized profit or loss for the position.
            realized_pnl (float): The realized profit or loss for the position.
            account_name (str): The account identifier associated with the position.

        How it works:
            - This method is triggered by the IB API when the `reqAccountUpdates` method is called.
            - It receives details about each position in the account, including the contract, position size,
            market price, market value, and profit/loss information.
            - The details are stored in the `self.positions` dictionary, keyed by the contract's symbol.
        
        Notes:
            - The `positions` dictionary acts as a centralized store for all positions in the account.
            - Each position is identified by the contract's symbol, ensuring unique keys for easy lookup.
            - This method is typically triggered multiple times, once for each position in the account.
        """
        portfolio_data = {
            "contract": contract,
            "symbol": contract.symbol,
            "position": position,
            "market_price": market_price,
            "market_value": market_value,
            "average_cost": average_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
        }
        self.positions[contract.symbol] = portfolio_data

    def pnl(self, request_id: int, daily_pnl: float, unrealized_pnl: float, realized_pnl: float) -> None:
        """
        Callback for receiving profit and loss (PnL) updates from the Interactive Brokers API.

        Args:
            request_id (int): A unique identifier for the PnL request.
            daily_pnl (float): The daily profit or loss of the account.
            unrealized_pnl (float): The unrealized profit or loss of the account, 
                                    calculated from open positions.
            realized_pnl (float): The realized profit or loss of the account, 
                                calculated from closed positions.

        How it works:
            - This callback is triggered by the IB API when a PnL update is received.
            - It creates a dictionary containing the daily, unrealized, and realized PnL.
            - The PnL data is stored in the `self.account_pnl` dictionary, keyed by the `request_id`.

        Notes:
            - The `self.account_pnl` attribute should be a dictionary initialized elsewhere 
            in the class to store PnL data.
            - This method ensures that PnL data for each `request_id` is stored separately, 
            allowing for multiple PnL requests to be tracked simultaneously.
        """
        pnl_data = {
            "daily_pnl": daily_pnl,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
        }
        self.account_pnl[request_id] = pnl_data
