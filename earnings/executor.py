"""This module contains all the logic that is used to execute Strangles trades
on the TD Ameritrade platform.
"""

from typing import List

from tda.orders.common import Duration, OptionInstruction, OrderType, Session
from tda.orders.generic import OrderBuilder

from earnings.broker import Broker


class Executor(Broker):
    def create_order_spec(self,
                          symbols: List[str],
                          price: float,
                          qty: int,
                          to_open: bool = True) -> dict:
        """Create an order template ready to be sent to TD.

        Args:
            symbols (List[str]): The list of symbols that make up the strangle.
            price (float): The price.
            qty (int): The quantity.
            to_open (bool, optional): Whether this is an opening or closing trade. Defaults to True.

        Returns:
            dict: The order template.
        """
        order_builder = OrderBuilder()
        order_builder.set_order_type(OrderType.LIMIT)
        order_builder.set_price(price)
        order_builder.set_duration(Duration.DAY)
        order_builder.set_session(Session.NORMAL)

        for symbol in symbols:
            order_builder.add_option_leg(
                OptionInstruction.SELL_TO_OPEN
                if to_open else OptionInstruction.BUY_TO_CLOSE, symbol, qty)

        order = order_builder.build()

        return order

    def place_trade(self, symbols: List[str], price: float, qty: int,
                    to_open: bool):
        """Places a trade on TD Ameritrade.

        Args:
            symbols (List[str]): List of option symbols that make up the strangle.
            price (float): The price for the spread.
            qty (int): The quantity.
            to_open (bool): Whether this is an opening or closing trade.
        """
        order_spec = self.create_order_spec(symbols,
                                            price,
                                            qty,
                                            to_open=to_open)
        self.client.place_order(self.ACCOUNT_ID, order_spec=order_spec)

    def replace_trade(self, order_id: str, symbols: List[str], price: float,
                      qty: int, to_open: bool):
        """Replaces an existing order on TD Ameritrade.

        Args:
            order_id (str): The order ID of the replaced order.
            symbols (List[str]): List of option symbols that make up the strangle.
            price (float): The price for the spread.
            qty (int): The quantity.
            to_open (bool): Whether this is an opening or closing trade.
        """
        order_spec = self.create_order_spec(symbols,
                                            price,
                                            qty,
                                            to_open=to_open)
        self.client.replace_order(self.ACCOUNT_ID,
                                  order_id=order_id,
                                  order_spec=order_spec)

    def cancel_trade(self, order_id: str):
        """Cancels a trade.

        Args:
            order_id (str): The trade ID of the trade to be cancelled.
        """
        self.client.cancel_order(account_id=self.ACCOUNT_ID, order_id=order_id)
