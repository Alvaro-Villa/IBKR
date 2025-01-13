from ibapi.contract import Contract, ComboLeg

def future(symbol: str, exchange: str, contract_month: str) -> Contract:
    """
    Creates a Contract object for a futures instrument.

    Args:
        symbol (str): The ticker symbol of the future.
        exchange (str): The primary exchange where the future is traded.
        contract_month (str): The contract month or last trade date in 'YYYYMM' format.

    Returns:
        Contract: A configured Contract object for the future.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.exchange = exchange
    contract.lastTradeDateOrContractMonth = contract_month
    contract.secType = "FUT"
    return contract

def stock(symbol: str, exchange: str, currency: str) -> Contract:
    """
    Creates a Contract object for a stock instrument.

    Args:
        symbol (str): The ticker symbol of the stock.
        exchange (str): The primary exchange where the stock is traded.
        currency (str): The currency in which the stock is denominated.

    Returns:
        Contract: A configured Contract object for the stock.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.exchange = exchange
    contract.currency = currency
    contract.secType = "STK"
    return contract

def option(symbol: str, exchange: str, contract_month: str, strike: float, right: str) -> Contract:
    """
    Creates a Contract object for an options instrument.

    Args:
        symbol (str): The ticker symbol of the underlying asset.
        exchange (str): The exchange where the option is traded.
        contract_month (str): The expiration month or last trade date in 'YYYYMM' format.
        strike (float): The strike price of the option.
        right (str): The option type ('C' for call, 'P' for put).

    Returns:
        Contract: A configured Contract object for the option.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.exchange = exchange
    contract.lastTradeDateOrContractMonth = contract_month
    contract.strike = strike
    contract.right = right
    contract.secType = "OPT"
    return contract

def forex(pair: str) -> Contract:
    """
    Creates a Contract object for a forex (currency pair) instrument.

    Args:
        pair (str): The forex pair in 'BASE/QUOTE' format (e.g., 'EUR/USD').

    Returns:
        Contract: A configured Contract object for the forex pair.
    """
    contract = Contract()
    base_currency, quote_currency = pair.split("/")
    contract.symbol = base_currency
    contract.secType = "CASH"
    contract.currency = quote_currency
    contract.exchange = "IDEALPRO"
    return contract

def combo_leg(contract_details, ratio, action):
    leg = ComboLeg()
    leg.conId = contract_details.contract.conId
    leg.ratio = ratio
    leg.action = action
    leg.exchange = contract_details.contract.exchange
    return leg

def spread(legs):
    contract = Contract()
    contract.symbol = "USD"
    contract.secType = "BAG"
    contract.currency = "USD"
    contract.exchange = "SMART"
    contract.comboLegs = legs
    return contract