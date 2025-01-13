from typing import Tuple
import threading
import time
import sqlite3
import empyrical as ep
from .wrapper import IBWrapper
from .client import IBClient
from .utils import (
    CREATE_BID_ASK_DATA,
    CREATE_OPEN_ORDERS,
    CREATE_TRADES
)


class IBApp(IBWrapper, IBClient):
    """
    A class that extends IBWrapper and IBClient to manage streaming market data
    and store it in an SQLite database.

    This class combines functionality from IBWrapper and IBClient to handle
    Interactive Brokers API interactions, including establishing connections,
    managing streaming tick-by-tick data, and storing market data into an SQLite database.

    Attributes:
        connection (sqlite3.Connection): A property that establishes and returns
            a connection to the SQLite database `tick_data.sqlite`.
    """

    def __init__(self, ip: str, port: int, client_id: int, account: str, interval: int = 5, risk_alerts: bool = False, **kwargs):
        """
        Initialize the IBApp instance.

        Args:
            ip (str): The IP address of the IB Gateway or TWS instance.
            port (int): The port number for connecting to IB Gateway or TWS.
            client_id (int): A unique client ID for the API connection.
            account (str): Account number for requesting account-level data.
            interval (int, optional): The time interval (in seconds) for streaming PnL data.
                                    Default is 5 seconds.

        Steps:
            - Initializes the IBWrapper and IBClient classes for API communication.
            - Stores the account identifier in `self.account`.
            - Creates the SQLite database table for storing bid/ask data.
            - Establishes a connection to the IB Gateway or TWS.
            - Starts a thread to run the API client's event loop in the background.
            - Starts another thread to stream unrealized PnL returns every `interval` seconds.

        Notes:
            - The event loop thread ensures that the API client remains responsive.
            - The PnL streaming thread provides periodic portfolio returns for performance analysis.

        Raises:
            - Connection errors if the connection to the IB Gateway or TWS fails.
        """
        IBWrapper.__init__(self)
        IBClient.__init__(self, wrapper=self)
        self.account = account
        self.create_table()
        self.connect(ip, port, client_id)
        threading.Thread(target=self.run, daemon=True).start()
        time.sleep(5)
        # threading.Thread(
        #   target=self.get_streaming_returns,
        #   args=(99, interval, "unrealized_pnl"),
        #   daemon=True,
        #).start()
        if risk_alerts:
            time.sleep(5)
            threading.Thread(
                target=self.watch_cvar,
                args=(kwargs["cvar_threshold"], interval),
                daemon=True
            ).start()

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Establish and return a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection to the `tick_data.sqlite` database.

        Notes:
            - The `isolation_level=None` parameter enables autocommit mode,
              where changes to the database are committed immediately after
              each statement without requiring `commit`.
        """
        return sqlite3.connect("data/strategy_1.sqlite", isolation_level=None)

    def create_table(self):
        """
        Create a database table to store bid/ask data if it does not exist.

        The table `bid_ask_data` includes the following columns:
            - timestamp: The time of the tick (datetime format).
            - symbol: The ticker symbol of the financial instrument.
            - bid_price: The current bid price.
            - ask_price: The current ask price.
            - bid_size: The size/volume of the bid.
            - ask_size: The size/volume of the ask.

        This method is called during initialization to ensure the table is ready
        before storing data.
        """
        cursor = self.connection.cursor()
        cursor.execute(CREATE_BID_ASK_DATA)
        cursor.execute(CREATE_OPEN_ORDERS)
        cursor.execute(CREATE_TRADES)

    def stream_to_sqlite(self, request_id: int, contract, run_for_in_seconds: int = 23400):
        """
        Stream tick-by-tick bid/ask data to an SQLite database for a specified duration.

        Args:
            request_id (int): The unique ID for the tick-by-tick data request.
            contract (Contract): The IB contract object specifying the financial instrument.
            run_for_in_seconds (int, optional): The duration in seconds to stream data
                (default: 6.5 hours or 23,400 seconds).

        Steps:
            - Establishes a database cursor.
            - Calculates the end time for data streaming.
            - Iterates over streaming data received from `get_streaming_data`.
            - Stores each tick as a row in the `bid_ask_data` table.
            - Stops streaming once the specified duration is reached.

        Notes:
            - The `stop_streaming_data` method is called after streaming ends
              to cancel the tick-by-tick data request.
        """
        cursor = self.connection.cursor()
        end_time = time.time() + run_for_in_seconds + 10  # Add buffer time

        for tick in self.get_streaming_data(request_id, contract):
            query = """
                INSERT INTO bid_ask_data (
                    timestamp, symbol, bid_price,
                    ask_price, bid_size, ask_size
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """
            values = (
                tick.timestamp_.strftime("%Y-%m-%d %H:%M:%S"),  # Format datetime
                contract.symbol,
                tick.bid_price,
                tick.ask_price,
                tick.bid_size,
                tick.ask_size,
            )
            cursor.execute(query, values)

            if time.time() >= end_time:  # Break the loop when the time limit is reached
                break

        self.stop_streaming_data(request_id)

    @property
    def cumulative_returns(self) -> float:
        """
        Calculate the cumulative returns of the portfolio.

        Returns:
            float: The cumulative return computed using the portfolio's periodic returns.

        Notes:
            - Empyrical's `cum_returns` method is used to calculate cumulative returns.
            - Assumes that `self.account_returns` contains a Pandas Series of periodic returns.
        """
        return ep.cum_returns(self.portfolio_returns, 1)

    @property
    def max_drawdown(self):
        """
        Calculate the maximum drawdown of the portfolio.

        Returns:
            float: The maximum drawdown, which is the largest peak-to-trough decline.

        Notes:
            - Empyrical's `max_drawdown` method is used for the calculation.
            - Drawdown measures the risk of loss from a portfolio's peak value.
        """
        return ep.max_drawdown(self.portfolio_returns)

    @property
    def volatility(self):
        """
        Calculate the volatility of the portfolio's returns.

        Returns:
            float: The standard deviation of the portfolio's returns (volatility).

        Notes:
            - Volatility is computed as the standard deviation of `self.account_returns`.
            - Assumes `self.account_returns` is a Pandas Series of periodic returns.
        """
        return self.portfolio_returns.std(ddof=1)

    @property
    def omega_ratio(self):
        """
        Calculate the Omega ratio of the portfolio's returns.

        Returns:
            float: The Omega ratio, which compares the probability-weighted returns 
                above a threshold to those below.
        """
        return ep.omega_ratio(self.portfolio_returns, annualization=1)

    @property
    def sharpe_ratio(self):
        """
        Calculate the Sharpe ratio of the portfolio's returns.

        Returns:
            float: The Sharpe ratio, which measures the return per unit of risk.
        """
        return self.portfolio_returns.mean() / self.portfolio_returns.std(ddof=1)

    @property
    def cvar(self) -> Tuple[float, float]:
        """
        Calculate the Conditional Value at Risk (CVaR) of the portfolio.

        Returns:
            Tuple[float, float]: A tuple containing:
                - The CVaR as a percentage.
                - The CVaR as an absolute value based on the Net Liquidation value.
        """
        net_liquidation = self.get_account_values("NetLiquidation")[0]
        cvar_ = ep.conditional_value_at_risk(self.portfolio_returns)
        return (cvar_, cvar_ * net_liquidation)


    def watch_cvar(self, threshold, interval):
        print("Watching CVaR in 60 seconds...")
        time.sleep(60)
        while True:
            cvar = self.cvar[1]
            if cvar < threshold:
                print(f"""Portfolio CVaR ({
                    cvar}) crossed threshold ({
                threshold})""")
            time.sleep(interval)