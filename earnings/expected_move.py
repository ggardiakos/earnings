"""Module that helps creating a straddle and calculating the expected move from it.

The expected move is an important figure when it comes to earnings plays using options,
we need to know how much the underlying asset is expected to move in order to pick
our strikes more efficiently.
"""

from typing import Optional

import pandas as pd

from earnings.option_chain import OptionChain


class Straddle(OptionChain):
    def __init__(self,
                 symbol: str,
                 dte: int = 0,
                 option_chain: Optional[pd.DataFrame] = None):
        """Constructor for the Straddle class.

        Args:
            symbol (str): The underlying symbol.
            dte (int, optional): The closest days to expiartion. Defaults to 0.
            option_chain (Optional[pd.DataFrame], optional): An option chain could be supplied to lower API calls and improve efficiency. Defaults to None.
        """
        super().__init__(symbol)
        if isinstance(option_chain, pd.DataFrame):
            self.option_chain = option_chain
        else:
            self.option_chain = self.build(dte,
                                           option_types='all',
                                           in_the_money=True,
                                           weeklies=True).dropna()

    def _build(self) -> pd.DataFrame:
        """Build the Straddle strategy.

        Made from 2 ATM options, the call and put ones.

        Returns:
            pd.DataFrame: The Straddle strategy.
        """
        idx_atm = self.option_chain['strike'].sub(
            self.underlying_price).abs().argmin()
        atm_strike = self.option_chain.loc[idx_atm, 'strike']
        straddle = self.option_chain[self.option_chain['strike'].eq(
            atm_strike)]
        straddle.reset_index(drop=True, inplace=True)
        return straddle

    @property
    def expected_move(self) -> float:
        """Calculates the expected move of the stock.

        Options traders use various methods to calculate the
        expected move, one of them is to take the ATM straddle
        and multiply it by 1.25.

        Returns:
            float: The expected move in points.
        """
        straddle = self._build()
        bid = straddle['bid'].sum()
        ask = straddle['ask'].sum()
        mid = (bid + ask) / 2
        expected_move = mid * 1.25
        expected_move = round(expected_move, 2)
        return expected_move
