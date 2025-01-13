import os

current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
os.chdir(parent_dir)

import pytest
from unittest.mock import MagicMock
from ibapi.contract import Contract
from ibapi.order import Order
from ibkr.app import IBApp

@pytest.fixture
def app():
    """
    Fixture para crear una instancia de IBApp para pruebas.
    """
    ib_app = IBApp(ip="127.0.0.1", port=7497, client_id=1, account="DU123456")
    ib_app.connect = MagicMock()
    ib_app.reqPnL = MagicMock()
    ib_app.cancelPnL = MagicMock()
    ib_app.reqMktData = MagicMock()
    ib_app.cancelMktData = MagicMock()
    ib_app.cancelTickByTickData = MagicMock()
    ib_app.placeOrder = MagicMock()
    return ib_app

def test_send_order(app):
    """
    Verifica que send_order envía una orden correctamente.
    """
    contract = Contract()
    order = Order()
    app.wrapper.nextValidOrderId = 1  # Simula un ID de orden válido

    order_id = app.send_order(contract, order)

    assert order_id == 1
    app.placeOrder.assert_called_with(orderId=1, contract=contract, order=order)
