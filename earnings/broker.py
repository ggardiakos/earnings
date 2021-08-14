"""This module contains the Broker class which is used to communicate with TD Ameritrade."""

import os
import pathlib
from typing import List

import pandas as pd
import tda
from utils import camel_to_snake

print(os.environ.get('TD_ACCOUNT_ID'))


class Broker:
    UTILS_PATH = os.path.abspath('utils')
    TOKEN_PATH = pathlib.Path(UTILS_PATH) / 'token'
    API_KEY = os.environ.get('TD_API_KEY')
    AUTH_KEY = f'{API_KEY}@AMER.OAUTHAP'
    REDIRECT_URI = os.environ.get('TD_REDIRECT_URI')
    ACCOUNT_ID = os.environ.get('TD_ACCOUNT_ID')

    def __init__(self):
        self.client = self.connect()

    def connect(self) -> tda.client.synchronous.Client:
        """Create an HTTP client that is used for making
        requests to TD Ameritrade.

        Returns:
            tda.client.synchronous.Client: Object used to communicate with TD.
        """
        try:
            client = tda.auth.client_from_token_file(self.TOKEN_PATH,
                                                     self.AUTH_KEY)
        except FileNotFoundError:
            from selenium import webdriver
            driver_path = pathlib.Path(self.UTILS_PATH) / 'geckodriver'
            with webdriver.Firefox(executable_path=driver_path) as driver:
                client = tda.auth.client_from_login_flow(
                    driver, self.AUTH_KEY, self.REDIRECT_URI, self.TOKEN_PATH)

        return client

    def get_option_chain(self, symbol: str) -> dict:
        """Get the raw option chains data for a symbol.

        Contains all expiraitons.

        Args:
            symbol (str): The underlying symbol.

        Returns:
            dict: The raw options data.
        """
        res = self.client.get_option_chain(symbol)
        data = res.json()
        assert data['status'] == 'SUCCESS'
        return data

    def get_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """Get current quotes for one or more symbols.

        Includes mark prices, net change, percent change and total volume.

        Args:
            symbols (List[str]): List of underlying symbols.

        Returns:
            pd.DataFrame: Quotes for the requested underlyings.
        """
        columns = {
            'mark': 'mark',
            'mark_change_in_double': 'mark_change',
            'mark_percent_change_in_double': 'mark_pct_change',
            'total_volume': 'volume'
        }
        res = self.client.get_quotes(symbols)
        quotes = pd.DataFrame(res.json()).T
        quotes.columns = [camel_to_snake(name) for name in quotes.columns]
        quotes = quotes[columns.keys()]
        quotes.rename(columns=columns, inplace=True)
        return quotes
