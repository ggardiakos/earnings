"""This modules provides an OptionChain class that helps retrieve, parse and build option chains
for underlying tickers
"""

import json
import os
from typing import Union

import pandas as pd

from earnings.broker import Broker


class OptionChain(Broker):
    def __init__(self, symbol: str):
        """Constructor for the option chain class.

        Args:
            symbol (str): The underlying's symbol.
        """
        super().__init__()
        self.raw_data = self.get_option_chain(symbol)
        self.underlying_price = self.raw_data['underlyingPrice']
        self.calls = self.raw_data['callExpDateMap']
        self.puts = self.raw_data['putExpDateMap']

        with open(os.path.join('utils', 'columns.json')) as f:
            self.COLUMNS, self.COLUMN_TYPES = json.load(f)

    def build(self,
              dte: int = 0,
              in_the_money: bool = False,
              weeklies: bool = True) -> pd.DataFrame:
        """Build the option chain for the underlying symbol.

        Args:
            dte (int, optional): Target days to expiration. Defaults to 45.
            in_the_money (bool, optional): Whether to include in-the-money options. Defaults to False.
            weeklies (bool, optional): Whether to include weekly options. Defaults to True.

        Returns:
            pd.DataFrame: A DataFrame containing the options chain, each option includes:
            - Strike
            - Option type
            - Bid
            - Ask
            - Last
            - Mark
            - Theoretical value
            - Implied volatility
            - Delta
            - Gamma
            - Theta
            - Vega
            - Volume
            - Open interest
            - Time value
            - Expiration date
            - Days to expiration
            - In the money
            - Multiplier
            - Symbol
            - Description
      """
        expiration_cycle = self._select_expiration(dte, weeklies)

        # Get the calls and puts from the selected expiration cycle
        calls = {k: v[0] for k, v in self.calls[expiration_cycle].items()}
        puts = {k: v[0] for k, v in self.puts[expiration_cycle].items()}

        calls = pd.DataFrame(calls).T.reset_index().rename(
            columns=self.COLUMNS)
        puts = pd.DataFrame(puts).T.reset_index().rename(columns=self.COLUMNS)
        option_chain = pd.concat([calls, puts])[self.COLUMNS.values()]

        # Convert data types
        option_chain['strike'] = option_chain['strike'].astype('float64')
        option_chain['option_type'] = option_chain['option_type'].astype(
            object)
        option_chain['expiration_date'] = pd.to_datetime(
            option_chain['expiration_date'], unit='ms').dt.strftime('%Y-%m-%d')
        option_chain = option_chain.astype(self.COLUMN_TYPES)

        if not in_the_money:
            option_chain = option_chain[option_chain['in_the_money'].eq(False)]

        # Sort by strikes
        option_chain.sort_values(by='strike', ascending=True, inplace=True)
        option_chain.reset_index(drop=True, inplace=True)

        return option_chain

    def _expirations(self, weeklies: bool = True) -> pd.DataFrame:
        """Returns the available expiration dates for this symbol.

        Args:
            weeklies (bool, optional): Whether to include weekly options. Defaults to True.

        Returns:
            pd.DataFrame: A DataFrame containing the expiration dates, days to expiration and
            type of expiration (monthly/weekly).
        """
        expirations = [e.split(':') for e in self.calls.keys()]
        expiration_types = [
            pd.Series(self.calls[k]).iloc[0][0]["expirationType"]
            for k in self.calls.keys()
        ]
        expirations = [
            expiration + ['MONTHLY' if expiration_type == 'R' else 'WEEKLY']
            for expiration, expiration_type in zip(expirations,
                                                   expiration_types)
        ]
        expirations = pd.DataFrame(expirations,
                                   columns=['date', 'dte', 'type'])

        if not weeklies:
            expirations = expirations[expirations['type'].ne('WEEKLY')]

        return expirations

    def _select_expiration(self,
                           dte: Union[int, str] = 0,
                           weeklies: bool = True) -> str:
        """Filters through the available expirations and chooses the
        one closest to the specified DTE.

        Args:
            dte (Union[int, str], optional): Target days to expiration. Defaults to 0.
            weeklies (bool, optional): Whether to include weekly options. Defaults to True.

        Returns:
            str: The requested expiration date, formatted for TD Ameritrade's API, for example:
            '2021-09-17:45'
        """
        expirations = self._expirations(weeklies)
        if dte == 'front':
            expiration = expirations.iloc[0]
        elif dte == 'back':
            expiration = expirations.iloc[1]
        else:
            closest_dte = expirations['dte'].astype(int).sub(
                dte).abs().argmin()
            expiration = expirations.iloc[closest_dte]

        expiration = ':'.join(expiration[['date', 'dte']].to_list())

        return expiration
