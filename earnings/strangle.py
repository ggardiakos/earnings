"""This module builds our Strangle strategy and makes sure it meets
our desired criteria.

We want a Strangle that covers the expected move, is liquid and has a
minimum amount of premium in it.
"""

from typing import Optional

import pandas as pd

from earnings.expected_move import Straddle
from earnings.option_chain import OptionChain


class Strangle(OptionChain):
    def __init__(self, symbol: str, dte: int = 0):
        """Constructor for the Strangle class.

        Args:
            symbol (str): The underlying symbol.
            dte (int, optional): The closest days to expiration. Defaults to 0.
        """
        super().__init__(symbol)
        self.option_chain = self.build(dte, in_the_money=False,
                                       weeklies=True).dropna()
        self.expected_move = Straddle(symbol, dte,
                                      self.option_chain).expected_move

    def covers_expected_move(self, call_strike: float, put_strike: float,
                             premium: float) -> bool:
        """Checks if a strangle is covering the expected move with its
        break even points, given the call strike, put strike and
        premium.

        Args:
            call_strike (float): [description]
            put_strike (float): [description]
            premium (float): [description]

        Returns:
            bool: [description]
        """
        top_break_even = call_strike + premium
        bottom_break_even = put_strike - premium
        top = self.underlying_price + self.expected_move
        bottom = self.underlying_price - self.expected_move
        covers = True if (top_break_even > top) and (
            bottom_break_even < bottom) else False

        return covers

    def _build(self, min_premium: float = 1.00) -> Optional[pd.DataFrame]:
        """Builds the strangle, returns a DataFrame with the two options
        if it exists and None if it doesn't.

        Args:
            min_premium (float, optional): The minimum premium to search for when building the strangle. Defaults to 1.00.

        Returns:
            Optional[pd.DataFrame]: The Strangle strategy.
        """
        calls = self.option_chain[self.option_chain['option_type'].eq(
            'CALL')].sort_values('strike', ascending=True)
        puts = self.option_chain[self.option_chain['option_type'].eq(
            'PUT')].sort_values('strike', ascending=False)

        strangles = []

        for call_strike, put_strike in zip(calls['strike'], puts['strike']):
            # Create the strangle
            call_option = calls[calls['strike'].eq(call_strike)].reset_index(
                drop=True)
            put_option = puts[puts['strike'].eq(put_strike)].reset_index(
                drop=True)
            strangle = pd.concat([put_option,
                                  call_option]).reset_index(drop=True)

            # Aggregate some info about the strangle
            bid = strangle['bid'].sum()
            ask = strangle['ask'].sum()
            mid = (ask + bid) / 2
            
            # We might wanna check the spreads later:
            # spread = ask - bid
            # relative_spread = spread / mid
            
            premium = (bid + ask) / 2

            if premium < min_premium:
                continue

            if self.covers_expected_move(call_strike, put_strike, premium):
                strangles.append(strangle)

        if not strangles:
            return None

        # Choose the strangle furthest away from the current price
        strangle = strangles[-1]

        return strangle
