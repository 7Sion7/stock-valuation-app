import os
import requests
from  helpers import get_date_range

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

PREV_DAY_URL = "https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
CLOSE_URL = "https://api.polygon.io/v1/open-close"
REF_URL = f"https://api.polygon.io/v3/reference/tickers"
DIVIDEND_URL = f"https://api.polygon.io/v3/reference/dividends"


def P_get_name (symbol):
    params = {
        "apiKey": POLYGON_API_KEY,
        "ticker": symbol,
        "limit": 5,
    }

    response = requests.get(REF_URL, params=params)
    if response.status_code != 200:
        print("Unable to fetch requested company", response.status_code)
        return None

    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        name = data['results'][0]['name']
        return name
    
    return None


def P_get_current_price(symbol):
    url = PREV_DAY_URL.format(ticker=symbol)

    params = {
        'apiKey': POLYGON_API_KEY,
        'ticker': symbol,
       
    }

    print("REMINDER: This is the close price of the day before, since this app is using a free api")

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("Unable to fetch api", response.status_code)
        return None

    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        previous_day_data = data['results'][0]
        closing_price = previous_day_data['c']
        return closing_price
    
    return None


def P_get_ticker_by_name(company_name):
    params = {
        'apiKey': POLYGON_API_KEY,
        'search': company_name,
    }
    response = requests.get(REF_URL, params=params)
    if response.status_code != 200:
        return None
    results = response.json().get('results', [])
    if not results:
        return None
    ticker = results[0]['ticker']  # Assuming the first result is the desired one
    return ticker

def P_get_company_logo(symbol):
    url = REF_URL.format(symbol)
    
    params = {
        'apiKey': POLYGON_API_KEY,
    }

    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"ERROR: {response.status_code}")
        return None
    
    data = response.json()
    if 'results' in data and 'branding' in data['results'] and 'logo_url' in data['results']['branding']:
        logo_url = data['results']['branding']['logo_url']
        return logo_url
    
    return None


def P_get_annual_returns_in_dividends(symbol):
    params = {
        "apiKey": POLYGON_API_KEY,
        "ticker": symbol,
        "limit": 1,
    }

    response = requests.get(DIVIDEND_URL, params=params)
    if response.status_code != 200:
        print("Unable to fetch data", response.status_code)
        return None#
    if len(response.json()['results']) < 1:
        return None
    frequency = response.json()['results'][0]['frequency']
    if frequency == 0:
        del params['limit']
    else:
        params['limit'] = 6 * frequency
    
    response = requests.get(DIVIDEND_URL, params=params)
    if response.status_code != 200:
        print("Unable to fetch dividends data", response.status_code)
        return None

    results = response.json()['results']

    start_year, current_year = get_date_range(6)

    returns = [{result['pay_date'][:4]: result['cash_amount']} for result in results if int(result['pay_date'][:4]) <= current_year or int(result['pay_date'][:4]) >= start_year]

    cash = [list(record.values())[0] for record in returns]

    average_yearly_return = (sum(cash) / 6)
    
    return average_yearly_return, returns