## Earnings

This package contains components that can be used to form an options trading strategy that sells strangles before earnings announcements.

This strategy has been researched for a while and has proven to generate positive expected return in the long term, I am sharing some of my work here.

## Features

- Web scraper for Finviz that serves as a scanner for companies reporting earnings.
- Get quotes for multiple tickers at once.
- Objects that are able to communicate with TD Ameritrade and retrieve account data, orders, positions
- Send orders, replace and cancel them.
- Request and parse option chains data into an easy-to-work-with DataFrame objects.
- Calculate expected moves.
- A Strangle class that combines a short call and put and meets entry criteria (covers expected move, minimum premium, ...)

From this you can easily construct a strategy that trades earnings announcements, you can also extend this package as much as you'd like, there is a lot to go to from here.

To use the TD Ameritrade API you'll need an account and an API key:
https://developer.tdameritrade.com/apis

And an account with Finviz.com.

## Installation

Clone the repo

```
git clone https://github.com/oriesh/earnings.git
```

Install the package

```
cd 'project directory here'
pip install .
```

Set environment variables

```
export TD_API_KEY="YOUR_API_KEY_HERE"
export TD_REDIRECT_URI="YOUR_REDIRECT_URI_HERE"
export TD_ACCOUNT_ID="YOUR_ACCOUNT_ID_HERE"
export FINVIZ_EMAIL="YOUR_FINVIZ_EMAIL_HERE"
export FINVIZ_PASSWORD="YOUR_FINVIZ_PASSWORD_HERE"
```

In order to work with TD Ameritrade's API, you'll need to generate an access token, the `Broker` class will do it for you through its `connect` method, once you sign in, the token will be placed in the `utils` folder, every token is valid for 90 days.

## Usage

See examples notebook (examples.ipynb in the root folder) for more detailed examples.

Quotes

```python
from earnings.broker import Broker

br = Broker()
quotes = br.get_quotes(['GOOG', 'AMZN'])
print(quotes)
```

Account

```python
from earnings.account import Account

acc = Account()

balances = acc.get_balances()
print(balances)

orders = acc.get_orders()
print(orders)

positions = acc.get_positions()
print(positions)
```

Screener

```python
from earnings.scanner import Scanner

scanner = Scanner()
earnings = scanner.earnings()
print(earnings)
```

Executing a trade

```python
from earnings.executor import Executor
from earnings.strangle import Strangle

executor = Executor()

# You can edit the _build method to change the selection criteria
strangle = Strangle('MSFT', dte=0)  # Front month expiration
strategy = strangle._build(min_premium=1.0)
print(strategy)

# Option symbols as seen in the 'symbol' column of the 'strategy' DataFrame above
executor.place_trade(['MSFT_082021P287.5', 'MSFT_082021C300'], price=2.15, quantity=1, to_open=True)
```

## Contributions

If you'd like to take this package further, feel free to open up a pull request :)

Hope you find this useful!
