from ibapi.order import Order

# Constants for order actions
BUY = "BUY"
SELL = "SELL"

def market(action: str, quantity: int) -> Order:
    """
    Creates a market order.

    Args:
        action (str): The order action, either 'BUY' or 'SELL'.
        quantity (int): The total quantity of the asset to buy or sell.

    Returns:
        Order: A configured Order object for a market order.
    """
    order = Order()
    order.action = action
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order

def limit(action: str, quantity: int, limit_price: float) -> Order:
    """
    Creates a limit order.

    Args:
        action (str): The order action, either 'BUY' or 'SELL'.
        quantity (int): The total quantity of the asset to buy or sell.
        limit_price (float): The price at which the order will be executed.

    Returns:
        Order: A configured Order object for a limit order.
    """
    order = Order()
    order.action = action
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = limit_price
    return order

def stop(action: str, quantity: int, stop_price: float) -> Order:
    """
    Creates a stop order.

    Args:
        action (str): The order action, either 'BUY' or 'SELL'.
        quantity (int): The total quantity of the asset to buy or sell.
        stop_price (float): The stop price at which the order will be triggered.

    Returns:
        Order: A configured Order object for a stop order.
    """
    order = Order()
    order.action = action
    order.orderType = "STP"
    order.auxPrice = stop_price  # Stop price is specified as auxPrice in IB API
    order.totalQuantity = quantity
    return order

def limit_stop(action: str, quantity: int, limit_price: float, stop_price: float) -> Order:
    """
    Creates a stop-limit order.

    Args:
        action (str): The order action, either 'BUY' or 'SELL'.
        quantity (int): The total quantity of the asset to buy or sell.
        limit_price (float): The limit price for the order.
        stop_price (float): The stop price at which the order will be triggered.

    Returns:
        Order: A configured Order object for a stop-limit order.
    """
    order = Order()
    order.action = action
    order.orderType = "STP LMT"
    order.lmtPrice = limit_price
    order.auxPrice = stop_price  # Stop price is specified as auxPrice in IB API
    order.totalQuantity = quantity
    return order

def bracket_order(action: str, quantity: float, take_profit_limit_price: float, stop_loss_price: float):
    """
    Crea un conjunto de órdenes tipo "bracket" (orden principal con órdenes dependientes de take profit y stop loss).

    Args:
        parentOrderId (int): El ID único de la orden principal (parent order).
        action (str): Acción de la orden principal, puede ser "BUY" (compra) o "SELL" (venta).
        quantity (Decimal): Cantidad del activo a negociar.
        limitPrice (float): Precio límite para la orden principal.
        takeProfitLimitPrice (float): Precio límite para la orden de take profit.
        stopLossPrice (float): Precio de activación para la orden de stop loss.

    Returns:
        list: Una lista que contiene tres objetos de tipo `Order` en el siguiente orden:
            1. Orden principal (parent order).
            2. Orden de take profit.
            3. Orden de stop loss.

    Notas:
        - La orden principal (parent order) es una orden de tipo "Limit" que establece el precio al que se ejecutará.
        - La orden de take profit (ganancia) se activa cuando el precio alcanza o supera el precio límite especificado.
        - La orden de stop loss (pérdida) se activa cuando el precio alcanza o cae por debajo del precio de activación.
        - Solo la última orden en la cadena (`stopLoss`) tiene el atributo `transmit=True`. Esto asegura que todas las órdenes se envíen juntas a Interactive Brokers.

    Ejemplo:
        Para crear una orden bracket que compre 100 acciones de un activo con un precio límite de 50.0,
        un take profit en 55.0, y un stop loss en 45.0:

        ```python
        orders = BracketOrder(
            parentOrderId=1001,
            action="BUY",
            quantity=100,
            limitPrice=50.0,
            takeProfitLimitPrice=55.0,
            stopLossPrice=45.0
        )
        ```

        Esta lista de órdenes puede luego enviarse a Interactive Brokers en el orden correcto.
    """
    # Orden principal (Parent Order)
    parent = Order()
    parent.action = action
    parent.orderType = "MKT"
    parent.totalQuantity = quantity
    # Asegurarse de no transmitir accidentalmente antes de completar las órdenes dependientes
    parent.transmit = False

    # Orden de Take Profit
    takeProfit = Order()
    takeProfit.orderId = parent.orderId + 1
    takeProfit.action = "SELL" if action == "BUY" else "BUY"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = take_profit_limit_price
    takeProfit.parentId = parent.orderId
    takeProfit.transmit = False

    # Orden de Stop Loss
    stopLoss = Order()
    stopLoss.orderId = parent.orderId + 2
    stopLoss.action = "SELL" if action == "BUY" else "BUY"
    stopLoss.orderType = "STP"
    # Precio de activación del stop loss
    stopLoss.auxPrice = stop_loss_price
    stopLoss.totalQuantity = quantity
    stopLoss.parentId = parent.orderId
    # Última orden; esta activa las órdenes anteriores
    stopLoss.transmit = True

    # Devuelve la lista de órdenes
    return [parent, takeProfit, stopLoss]
