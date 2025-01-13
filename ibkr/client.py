import time
import pandas as pd
from typing import List, Generator

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order

from .order import BUY, SELL
from .utils import Tick, TRADE_BAR_PROPERTIES, DEFAULT_MARKET_DATA_ID, DEFAULT_CONTRACT_ID

class IBClient(EClient):
    def __init__(self, wrapper):
        """
        Initialize the IBClient.

        Args:
            wrapper (EWrapper): The wrapper object that handles API callbacks.
        """
        EClient.__init__(self, wrapper)

    def resolve_contract(self, contract, request_id=DEFAULT_CONTRACT_ID):
            self.reqContractDetails(reqId=request_id,
                contract=contract)
            time.sleep(2)
            self.contractDetailsEnd(reqId=request_id)
            return self.resolved_contract
    
    def cancel_all_orders(self) -> None:
        """
        Cancels all active orders globally.

        How it works:
            - Sends a global cancel request to the IB API using `reqGlobalCancel`.
            - This cancels all orders associated with the connected account.

        Notes:
            - Use with caution as it cancels all active orders, including those 
              placed manually or by other clients using the same account.
        """
        self.reqGlobalCancel()

    def cancel_order_by_id(self, order_id: int) -> None:
        """
        Cancels a specific order by its unique order ID.

        Args:
            order_id (int): The unique ID of the order to be canceled.

        How it works:
            - Sends a cancel request to the IB API for the specified order ID.
            - Optionally, a manual cancellation time can be provided (left empty here).

        Notes:
            - The `order_id` should match an existing order in the system.
            - Order cancellation is subject to confirmation via API callbacks, such as 
              `orderStatus` or `openOrder`.
        """
        self.cancelOrder(orderId=order_id, manualCancelOrderTime="")

    def update_order(self, contract: Contract, order: Order, order_id: int) -> int:
        """
        Updates an existing order by canceling it and placing a new one with the updated details.

        Args:
            contract (Contract): The financial instrument associated with the order.
            order (Order): The updated order details, such as action (BUY/SELL), 
                           type (e.g., LMT, MKT), total quantity, and limit price.
            order_id (int): The unique ID of the existing order to be updated.

        Returns:
            int: The unique ID of the newly placed order.

        How it works:
            - Cancels the existing order using `cancel_order_by_id`.
            - Sends a new order using the `send_order` method, which generates a new order ID.

        Notes:
            - The new order ID is returned and can be used to track the new order's status.
            - Ensure that the contract and order objects are updated correctly before calling this method.
        """
        self.cancel_order_by_id(order_id)
        return self.send_order(contract, order)

    def send_order(self, contract: Contract, order) -> int:
        """
        Sends an order to the Interactive Brokers API.

        Args:
            contract (Contract): The financial instrument associated with the order. 
                                This includes details like symbol, security type, 
                                exchange, and currency.
            order (Order): The details of the order, such as the action (BUY/SELL), 
                        order type (e.g., LMT, MKT), total quantity, and limit price.

        Returns:
            int: The unique order ID assigned to the submitted order.

        How it works:
            - Retrieves the next valid order ID from the `nextValidOrderId` attribute 
            of the wrapper (set by the IB API when the connection is established).
            - Places the order by calling the `placeOrder` method of the IB API.
            - Sends a `reqIds(-1)` request to the server to increment and fetch 
            the next valid order ID for subsequent orders.
        """
        order_id = self.wrapper.nextValidOrderId
        self.placeOrder(orderId=order_id, contract=contract, order=order)
        self.reqIds(-1)
        return order_id
    
    def order_value(self, contract, order_type, value, **kwargs):
        quantity = self._calculate_order_value_quantity(
            contract, value)
        order = order_type(quantity=quantity, **kwargs)
        return self.send_order(contract, order)
    
    def order_target_quantity(self, contract, order_type, target, **kwargs):
        quantity=self._calculate_order_target_quantity(contract,
            target)
        order = order_type(
            action=SELL if quantity < 0 else BUY,
            quantity=abs(quantity),
            **kwargs
        )
        return self.send_order(contract, order)
    
    def _calculate_order_target_quantity(self, contract, target):
        positions = self.get_positions()
        if contract.symbol in positions.keys():
            current_position = positions[
                contract.symbol]["position"]
            target -= current_position
        return int(target)

    def order_percent(self, contract, order_type, percent, **kwargs):
        quantity = self._calculate_order_percent_quantity(
            contract, percent)
        order = order_type(quantity=quantity,
            **kwargs)
        return self.send_order(contract, order)
    
    def _calculate_order_percent_quantity(self, contract, percent):
        net_liquidation_value = self.get_account_values(
            key="NetLiquidation")[0]
        value = net_liquidation_value * percent
        return self._calculate_order_value_quantity(contract, value)
    
    def order_target_value(self, contract, order_type, target, **kwargs):
        target_quantity = self._calculate_order_value_quantity(
            contract, target)
        quantity = self._calculate_order_target_quantity(contract,
            target_quantity)
        order = order_type(
            action=SELL if quantity < 0 else BUY,
            quantity=abs(quantity),
            **kwargs
        )
        return self.send_order(contract, order)
    
    def _calculate_order_value_quantity(self, contract, value):
        last_price = self.get_market_data(
            request_id=DEFAULT_MARKET_DATA_ID,
                contract=contract, tick_type=1)
        multiplier = contract.multiplier if contract.multiplier != "" else 1
        return int(value / (last_price * multiplier))
    
    def order_target_percent(self, contract, order_type, target, **kwargs):
        quantity = self._calculate_order_target_percent_quantity(
            contract, target)
        order = order_type(
            action=SELL if quantity < 0 else BUY,
            quantity=abs(quantity),
            **kwargs
        )
        return self.send_order(contract, order)
    
    def _calculate_order_target_percent_quantity(self, contract, target):
        target_quantity = self._calculate_order_percent_quantity(
            contract, target)
        return self._calculate_order_target_quantity(contract, target_quantity)
        
    def get_historical_data(self, request_id: int, contract: Contract, duration: str, bar_size: str) -> pd.DataFrame:
        """
        Request historical market data for a specific financial instrument.

        Args:
            request_id (int): Unique request ID to identify the data request.
            contract (Contract): IB Contract object specifying the financial instrument.
            duration (str): The duration for which to request data (e.g., "1 D", "1 W").
            bar_size (str): The bar size for the data (e.g., "1 min", "5 mins").

        Returns:
            pd.DataFrame: A DataFrame containing the historical data, with columns 
                          ["open", "high", "low", "close", "volume"] and the index as timestamps.
        """
        self.reqHistoricalData(
            reqId=request_id,
            contract=contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT",
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[],
        )
        time.sleep(5)

        # Determine the date format based on the bar size
        bar_sizes = ["day", "D", "week", "W", "month"]
        if any(x in bar_size for x in bar_sizes):
            fmt = "%Y%m%d"
        else:
            fmt = "%Y%m%d %H:%M:%S %Z"

        # Extract historical data for the given request ID
        data = self.historical_data[request_id]

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=TRADE_BAR_PROPERTIES)
        df.set_index(pd.to_datetime(df.time, format=fmt), inplace=True)
        df.drop("time", axis=1, inplace=True)
        df["symbol"] = contract.symbol
        df.request_id = request_id

        return df

    def get_historical_data_for_many(
        self, request_id: int, contracts: List[Contract], duration: str, bar_size: str, col_to_use: str = "close"
    ) -> pd.DataFrame:
        """
        Request historical market data for multiple financial instruments.

        Args:
            request_id (int): Initial request ID. It will increment for each contract.
            contracts (List[Contract]): A list of IB Contract objects specifying the financial instruments.
            duration (str): The duration for which to request data (e.g., "1 D", "1 W").
            bar_size (str): The bar size for the data (e.g., "1 min", "5 mins").
            col_to_use (str, optional): The column to use for pivoting the DataFrame (default: "close").

        Returns:
            pd.DataFrame: A pivoted DataFrame where the index is timestamps and the columns are symbols.
        """
        dfs = []
        for contract in contracts:
            data = self.get_historical_data(request_id, contract, duration, bar_size)
            dfs.append(data)
            request_id += 1
        
        # Combine all DataFrames and pivot
        return (
            pd.concat(dfs)
            .reset_index()
            .drop_duplicates()
            .pivot(index="time", columns="symbol", values=col_to_use)
        )


    def get_market_data(self, request_id: int, contract: Contract, tick_type: int = 4) -> float:
        """
        Fetch specific market data (e.g., last traded price) for a given contract.

        Args:
            request_id (int): A unique identifier for the data request.
            contract (Contract): The IB Contract object specifying the financial instrument.
            tick_type (str, optional): The type of market data tick to retrieve (default: 4, last traded price).

        Returns:
            float: The requested market data (e.g., price) as a float.

        How it works:
            - Initiates a market data request for the given contract using `reqMktData`.
            - Pauses for 5 seconds to allow data reception and processing.
            - Cancels the market data request to free up the request ID.
            - Retrieves the specific tick type data from the `market_data` dictionary.

        Note:
            The tickPrice callback should populate the `market_data` dictionary with received data.
            Ensure `market_data` is properly initialized in the wrapper.
        """
        self.reqMktData(
            reqId=request_id,
            contract=contract,
            genericTickList="4",
            snapshot=True,
            regulatorySnapshot=False,
            mktDataOptions=[],)
        time.sleep(2)  # Allow time for data to be received
        return self.market_data.get(request_id, {}).get(tick_type)
    

    def get_streaming_data(self, request_id: int, contract: Contract) -> Generator[Tick, None, None]:
        """
        Stream live tick-by-tick market data for a specific contract.

        Args:
            request_id (int): A unique identifier for the data stream request.
            contract (Contract): The IB Contract object specifying the financial instrument.

        Yields:
            Tick: A `Tick` dataclass instance containing bid/ask prices, sizes, and timestamps.

        How it works:
            - Initiates a tick-by-tick data stream using `reqTickByTickData`.
            - Continuously listens for market tick updates in real-time.
            - Uses the `stream_event` (assumed to be implemented) to synchronize data arrival.
            - Returns the data as a `Tick` object whenever new data is available.

        Notes:
            - The method is a generator that yields new tick data indefinitely.
            - The `streaming_data` dictionary and `stream_event` should be properly handled in the wrapper.
        """
        self.reqTickByTickData(
            reqId=request_id,
            contract=contract,
            tickType="BidAsk",  # Request bid/ask tick type
            numberOfTicks=0,    # Infinite stream
            ignoreSize=True,    # Ignore tick size filter
        )
        time.sleep(10)  # Allow some initial data to arrive

        while True:
            if self.stream_event.is_set():  # Wait for new data
                yield Tick(*self.streaming_data[request_id])  # Yield the tick data
                self.stream_event.clear()  # Reset the event flag

    def stop_streaming_data(self, request_id: int) -> None:
        """
        Stop the tick-by-tick streaming data for a specific request ID.

        Args:
            request_id (int): The unique identifier for the tick-by-tick data request.

        How it works:
            - Cancels the tick-by-tick data stream using `cancelTickByTickData`.
            - Frees up the request ID for future use.
        """
        self.cancelTickByTickData(reqId=request_id)

    def get_account_values(self, key: str = None) -> dict:
        """
        Retrieve account values from the Interactive Brokers API.
        For a complete list of account values and their descriptions, see the following URL: 
        https:// interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper. html#ae15a34084d9f26f279abd0bdeab1b9b5.

        Args:
            key (str, optional): A specific key for which to retrieve the account value.
                                If `None`, all account values are returned.
                                Examples of keys include "NetLiquidation", "BuyingPower", etc.

        Returns:
            dict: 
                - If `key` is provided, returns the value associated with the given key.
                - If `key` is not provided, returns the entire dictionary of account values.

        How it works:
            - Sends a request to the IB API using `reqAccountUpdates` to fetch account values.
            - Pauses for 2 seconds to allow the callback to populate `self.account_values`.
            - If a specific key is provided, it retrieves the corresponding value from `self.account_values`.
            - If no key is provided, it returns the entire dictionary of account values.
        
        """
        self.reqAccountUpdates(True, self.account)
        time.sleep(2)
        if key:
            return self.account_values[key]
        return self.account_values
    
    def get_positions(self) -> dict:
        """
        Retrieve the current positions in the account.

        Returns:
            dict: A dictionary containing details about all positions, keyed by symbol.

        How it works:
            - Requests portfolio updates using `reqAccountUpdates`.
            - Pauses execution for 2 seconds to allow the `updatePortfolio` callback to populate `self.positions`.
            - Returns the `self.positions` dictionary containing the current positions in the account.
        """
            
        self.reqAccountUpdates(True, self.account)
        time.sleep(2)
        return self.positions
    
    def get_pnl(self, request_id: int) -> dict:
        """
        Request and retrieve the profit and loss (PnL) data for the account.

        Args:
            request_id (int): A unique identifier for the PnL request.

        Returns:
            dict: A dictionary containing the daily, unrealized, and realized PnL for the account, 
                structured as:
                {
                    "daily_pnl": float,
                    "unrealized_pnl": float,
                    "realized_pnl": float
                }

        How it works:
            - Sends a request to the IB API for PnL data using the `reqPnL` method, 
            passing the `request_id` and the account identifier (`self.account`).
            - Pauses execution for 2 seconds to allow the `pnl` callback to populate the 
            `self.account_pnl` dictionary with the requested data.
            - Returns the PnL data stored in `self.account_pnl`, keyed by the given `request_id`.

        Notes:
            - This method depends on the `pnl` callback being implemented correctly to handle 
            and store the PnL data in `self.account_pnl`.
            - Unrealized PnL refers to potential profit or loss from open positions, 
            while realized PnL refers to profit or loss from closed positions.
        """
        self.reqPnL(request_id, self.account, "")  # Send request for PnL data
        time.sleep(2)  # Allow time for the callback to populate `self.account_pnl`
        self.cancelPnL(reqId=request_id)
        return self.account_pnl
    
    def get_streaming_pnl(self, request_id: int, interval: int = 60, pnl_type: str = "unrealized_pnl") -> Generator[dict, None, None]:
        """
        Stream periodic PnL data for real-time portfolio performance monitoring.

        Args:
            request_id (int): The unique identifier for the PnL request.
            interval (int, optional): The time interval (in seconds) between PnL updates. 
                                    Default is 60 seconds. Minimum interval is 5 seconds.
            pnl_type (str, optional): The type of PnL to stream. Can be "unrealized_pnl" or 
                                    "realized_pnl". Default is "unrealized_pnl".

        Yields:
            dict: A dictionary containing:
                - "date": The current timestamp.
                - "pnl": The requested PnL value (unrealized or realized).

        How it works:
            - Adjusts the `interval` to ensure a minimum of 5 seconds between updates.
            - Calls `get_pnl` to fetch the latest PnL data for the given `request_id`.
            - Yields a dictionary with the current timestamp and the requested PnL type.
            - Continues streaming PnL data indefinitely, sleeping for the specified interval 
            between updates.

        Notes:
            - The `pnl` callback must populate the `self.account_pnl` dictionary with the 
            necessary data for this method to work.
            - Streaming PnL is useful for monitoring portfolio performance in real-time.
        """
        interval = max(interval, 5) - 2
        while True:
            pnl = self.get_pnl(request_id=request_id)
            yield {"date": pd.Timestamp.now(), "pnl": pnl[request_id].get(pnl_type) if pnl else None}
            time.sleep(interval)

    def get_streaming_returns(self, request_id: int, interval: int, pnl_type: str) -> None:
        """
        Stream periodic portfolio returns for performance and risk analysis.

        Args:
            request_id (int): The unique identifier for the PnL request.
            interval (int): The time interval (in seconds) between updates.
            pnl_type (str): The type of PnL to use for calculating returns 
                            (e.g., "unrealized_pnl", "realized_pnl").

        Steps:
            - Streams PnL data using `get_streaming_pnl`.
            - Computes percentage returns based on the streamed PnL data.
            - Updates the `self.portfolio_returns` attribute with the calculated returns.

        Notes:
            - Returns are calculated as percentage changes in PnL values over time.
            - This method runs indefinitely and updates `self.portfolio_returns` in real-time.
            - Useful for live portfolio performance monitoring and risk management.

        Example Usage:
            # Stream returns for unrealized PnL every 60 seconds
            client.get_streaming_returns(request_id=1, interval=60, pnl_type="unrealized_pnl")

        Raises:
            ValueError: If the PnL type is invalid or unsupported.
        """
        self.returns = pd.Series(dtype=float)
        for snapshot in self.get_streaming_pnl(
            request_id=request_id, interval=interval, pnl_type=pnl_type
        ):
            self.returns.loc[snapshot["date"]] = snapshot["pnl"] if snapshot["pnl"] != 0 else 0.001
            if len(self.returns) > 1:
                self.portfolio_returns = self.returns.pct_change(fill_method=None).dropna()
