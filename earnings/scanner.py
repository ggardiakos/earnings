"""Scraper for the Finviz screener.

Finviz.com has one of the best stock screeners in the web, but they do not provide an SDK
for developers to easily interract with their data.

For this purpose I have built this simple tool, it scrapes the data off the various screeners,
I provided 2 of them so far:
1) Movers
2) Earnings

The script can be editted and extended further.

You will need to be logged into Finviz for this to work, preferably with an active subscription,
please set your login details as an environment variable:

FINVIZ_EMAIL - for your login email
FINVIZ_PASSWORD - for your login password

Hope you find this tool useful.
"""

import os
from typing import Dict, List

import numpy as np
import pandas as pd
import requests
import user_agent
from bs4 import BeautifulSoup


class Scanner:
    def __init__(self):
        self.login_url = 'https://finviz.com/login_submit.ashx'
        self.screener_url = 'https://finviz.com/screener.ashx'
        self.headers = {
            'user-agent': user_agent.generate_user_agent(os='linux')
        }

    @property
    def login_details(self) -> Dict[str, str]:
        """Prepares the login form details.

        Raises:
            Exception: If the required environment variables are not set.

        Returns:
            Dict[str, str]: The login form details in JSON format (dict), ready to be sent to Finviz.
        """
        email = os.environ.get('FINVIZ_EMAIL')
        password = os.environ.get('FINVIZ_PASSWORD')
        if not email or not password:
            raise Exception(
                'Please set required env. variables ( FINVIZ_EMAIL , FINVIZ_PASSWORD )'
            )
        return {'email': email, 'password': password, 'remember': 'true'}

    def earnings(self) -> pd.DataFrame:
        """Retrieves the stocks that report earnings today.

        Returns:
            pd.DataFrame: DataFrame containing all the relevant stocks, the fields include:
            symbol, market cap (billions), price, changes (decimal), time (before/after market)
        """
        earnings = self._get_earnings()
        earnings = self._clean_earnings(earnings)
        return earnings

    def _get_earnings(self) -> List[List[str]]:
        """Get the raw earnings reports data from Finviz.

        Returns:
            List[List[str]]: Data grouped as a nested list, each item contains one row of data.
        """
        with requests.Session() as session:
            # Post login form
            session.post(self.login_url,
                         data=self.login_details,
                         headers=self.headers)

            # Choose screener URLs, fields and other parameters
            target_params = [{
                'url': self.screener_url,
                'v': '152',
                's': 'n_earningsbefore',
                'f': 'sh_price_o15,sh_relvol_o1',
                'o': '-marketcap',
                'c': '0,1,6,65,66,68'
            }, {
                'url': self.screener_url,
                'v': '152',
                's': 'n_earningsafter',
                'f': 'sh_price_o15,sh_relvol_o1',
                'o': '-marketcap',
                'c': '0,1,6,65,66,68'
            }]

            earnings = []

            for params in target_params:
                url = params.pop('url')
                req = session.get(url, params=params, headers=self.headers)
                soup = BeautifulSoup(req.content, 'lxml')
                data = [
                    td.a.text
                    for td in soup.find_all('td',
                                            class_='screener-body-table-nw')
                ]
                cols = 6
                # Grouping the data by its intended columns
                earnings += [
                    data[n + 1:n + cols] for n in range(0, len(data), cols)
                ]

        return earnings

    def _clean_earnings(self, earnings: List[List[str]]) -> pd.DataFrame:
        """Transforms raw earnings data into an easy-to-work-with DataFrame object.

        Args:
            earnings (List[List[str]]): The raw data, as retrieved from Finviz.

        Returns:
            pd.DataFrame: The earnings DataFrame, sorted by market caps.
        """
        earnings = pd.DataFrame(
            earnings,
            columns=['symbol', 'market_cap', 'price', 'change', 'time'])
        earnings['price'] = earnings['price'].astype('float64')
        earnings['change'] = earnings['change'].str.replace(
            '%', '').astype('float64') / 100
        earnings['market_cap'] = self._transform_market_caps(
            earnings['market_cap'])

        # Seperating date from time
        times = earnings['time'].str.split('/', expand=True)
        earnings['time'] = times[1].replace({'a': 'AMC', 'b': 'BMO'})

        # Filtering reports
        earnings = earnings[earnings['time'].eq('AMC')]  # Only AMC reports
        earnings = earnings[earnings['market_cap'].gt(10)]  # Large cap stocks

        # Sorting by market cap
        earnings.sort_values(by=['market_cap'], ascending=False, inplace=True)
        earnings.reset_index(drop=True, inplace=True)

        return earnings

    def _transform_market_caps(self, market_caps: pd.Series) -> pd.Series:
        """Transform a string vector representing market caps into 
        floating point numbers where every 1 point represents 1 billion.
        
        For example:
        '10.42B' becomes 10.42

        Args:
            market_caps (pd.Series): The original market caps series.

        Returns:
            pd.Series: The transformed market caps series.
        """
        m = {'K': 3, 'M': 6, 'B': 9, 'T': 12}
        market_caps = market_caps.replace('-', np.nan)
        market_caps = [
            float(i[:-1]) * 10**m[i[-1]] / 1_000_000_000 for i in market_caps
        ]
        return market_caps
