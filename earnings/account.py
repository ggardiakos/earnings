"""This module contains the Account class which is used to get balances, orders and positions from
the account."""

import datetime

import pandas as pd
from utils import camel_to_snake, flatten

from earnings.broker import Broker


class Account(Broker):
    def get_balances(self) -> pd.Series:
        """Get the account balances.

        Includes:
        - Balance (liquidation value)
        - Equity
        - Free margin
        - Used margin

        Returns:
            pd.Series: The account balances.
        """
        res = self.client.get_account(account_id=self.ACCOUNT_ID)
        data = res.json()['securitiesAccount']['currentBalances']
        account = pd.Series(data)
        fields = {
            'liquidationValue': 'balance',
            'equity': 'equity',
            'availableFunds': 'free_margin',
            'maintenanceRequirement': 'used_margin',
        }
        account = account.loc[fields].rename(fields)
        return account

    def get_orders(self) -> pd.DataFrame:
        """Gets the current orders of the account.

        Returns:
            pd.DataFrame: The current orders.
        """
        res = self.client.get_account(self.ACCOUNT_ID,
                                      fields=self.client.Account.Fields.ORDERS)
        orders = res.json()['securitiesAccount']['orderStrategies']
        orders = pd.DataFrame(orders)
        orders.columns = [camel_to_snake(c) for c in orders.columns]
        orders.drop([
            'order_strategy_type', 'requested_destination',
            'destination_link_name', 'editable', 'account_id'
        ],
                    axis=1,
                    inplace=True)
        return orders

    def get_positions(self) -> pd.DataFrame:
        """Gets the current positions of the account.

        Returns:
            pd.DataFrame: The open positions.
        """
        res = self.client.get_account(
            self.ACCOUNT_ID, fields=self.client.Account.Fields.POSITIONS)
        data = [
            flatten(position)
            for position in res.json()['securitiesAccount']['positions']
        ]
        cols = {
            'shortQuantity': 'qty_short',
            'longQuantity': 'qty_long',
            'averagePrice': 'price',
            'currentDayProfitLoss': 'pal_day',
            'instrument_assetType': 'asset_type',
            'instrument_symbol': 'symbol',
            'instrument_putCall': 'option_type',
            'instrument_underlyingSymbol': 'underlying',
            'marketValue': 'value',
            'maintenanceRequirement': 'buying_power',
        }
        positions = pd.DataFrame(data)[cols.keys()].rename(cols, axis=1)
        positions['qty'] = positions['qty_long'] - positions['qty_short']

        expiration_dates_and_strikes = positions['symbol'].str.split(
            r'_', expand=True)[1].str.split(r'[CP]', expand=True)
        positions['expiration_date'] = expiration_dates_and_strikes[0].apply(
            lambda dt: datetime.datetime.strptime(dt, '%m%d%y').strftime(
                '%d%b%y').upper() if dt else dt)
        positions['strike'] = expiration_dates_and_strikes[1]

        positions.sort_values(by=['expiration_date', 'underlying', 'strike'],
                              ascending=[True, True, False],
                              inplace=True)
        positions.reset_index(drop=True, inplace=True)
        equity_positions = positions['underlying'].isna()
        positions.loc[equity_positions,
                      'underlying'] = positions.loc[equity_positions, 'symbol']

        order = [
            'underlying',
            'asset_type',
            'qty',
            'option_type',
            'expiration_date',
            'strike',
            'price',
            'value',
            'pal_day',
            'buying_power',
        ]

        return positions[order]
