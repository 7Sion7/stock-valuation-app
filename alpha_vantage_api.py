import os
import requests
from helpers import get_date_range
from collections import Counter

API_KEY = os.getenv("ALPHA_API_KEY")

URL = "https://www.alphavantage.co/query"


def AV_get_ticker_by_name(company_name):
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': company_name,
        'apikey': API_KEY,
    }
    response = requests.get(URL, params=params)
    if 'Information' in response.json():
        print("Limit of 25 requests daily exceeded")
        return None
    if response.status_code != 200:
        print("Unable to get ticker symbol", response)
        return None
    results = response.json().get('bestMatches', [])
    if not results:
        print("No results:", results)
        return None
    
    ticker = results[0]['1. symbol']  
    return ticker

def AV_get_name(symbol):
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': symbol,
        'apikey': API_KEY,
    }
    response = requests.get(URL, params=params)
    if 'Information' in response.json():
        print("Limit of 25 requests daily exceeded")
        return None
    if response.status_code != 200:
        return f"ERROR: {response.status_code}"
    
    matches = response.json().get('bestMatches', [])
    if not matches:
        return None
    name = matches[0]['2. name']
    return name

def AV_get_current_price(symbol):
    params = {
        'apikey': API_KEY,
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '1min',
        'limit': 1,
    }

    response = requests.get(URL, params=params)

    if response.status_code != 200:
        print("Unable to fetch price", response.status_code)
        return None
    if 'Information' in response.json():
        print("Limit of 25 requests daily exceeded")
        return None
    time_series = response.json().get('Time Series (1min)', {})
    if not time_series:
        print("Unable to find times series", time_series)
        return None
    latest_key = sorted(time_series.keys())[-1]
    price = float(time_series[latest_key]['4. close'])

    return price

def AV_get_dividends_for_year(symbol):
    params = {
        'apikey': API_KEY,
        'symbol': symbol,
        'function': "DIVIDENDS"
    }
    first_year, current_year = get_date_range(6)    

    response = requests.get(URL, params=params)
    if 'Information' in response.json():
        print("Limit of 25 requests daily exceeded")
        return None
    if response.status_code == 200:
        data = response.json().get('data', [])
        if not data:
            return None
        dividends = [{dividend['ex_dividend_date'][:4]: float(dividend['amount'])}for dividend in data if int(dividend['ex_dividend_date'][:4]) >= first_year and int(dividend['ex_dividend_date'][:4]) <= current_year]
        combined_data = Counter()
        for d in dividends:
            combined_data.update(d)

        combined_data = dict(combined_data)
        sum_of_dividends = sum(combined_data.values())

        return sum_of_dividends / len(combined_data), dividends
    else:
        return None
