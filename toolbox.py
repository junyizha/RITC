import signal
import requests
from time import sleep


class ApiException(Exception):
    pass


def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True


# port 9999 API KEY: WDTA5SNM
API_KEY = {"X-API-Key": "UJM3CFTD"}
shutdown = False
news_id = 0


def get_case(session):
    resp = session.get("http://localhost:9999/v1/case")
    if resp.ok:
        case = resp.json()
        return case
    raise ApiException("Authorization error. Please check API_KEY.")


def get_orders(session):
    resp = session.get("http://localhost:9999/v1/orders")
    if resp.ok:
        orders = resp.json()
        return orders
    raise ApiException("Authorization error. Please check API_KEY.")


def get_tenders(session):
    resp = session.get("http://localhost:9999/v1/tenders")
    if resp.ok:
        tenders = resp.json()
        print(tenders)
        return tenders
    raise ApiException("Authorization error. Please check API_KEY.")


def get_history(session):
    resp = session.get("http://localhost:9999/v1/history")
    if resp.ok:
        history = resp.json()
        print(history)
        return history
    raise ApiException("Authorization error. Please check API_KEY.")


def get_book(session, ticker):
    resp = session.get(f"http://localhost:9999/v1/securities/book?ticker={ticker}")
    if resp.ok:
        book = resp.json()
        return book
    raise ApiException("Authorization error. Please check API_KEY.")


# return the most recent volatility, if its the beginning of the game, its 20%
def get_curr_volatility(session):
    resp = session.get("http://localhost:9999/v1/news")
    if resp.ok:
        news = resp.json()
        assert (len(news) != 0)
        # if its just first two news
        if len(news) in (1, 2, 3):
            return 0.2
        else:
            curr = news[0]
            if 'News' in curr['headline']:
                curr = news[1]
            return int(curr['body'][-3:-1]) / 100


def get_predicted_volatility(session):
    resp = session.get("http://localhost:9999/v1/news")
    if resp.ok:
        news = resp.json()
        assert (len(news) != 0)
        # if its just first two news
        if len(news) in (1, 2):
            return None, None
        else:
            curr = news[0]
            if 'Announcement' in curr['headline']:
                curr = news[1]
            lower = int(curr['body'][-32:-30]) / 100
            upper = int(curr['body'][-26:-24]) / 100
        return lower, upper


################################################################
# from calendar_arbitrage
# get return a list of tickers, only those options expire in one month
def get_tickers(session) -> list:
    resp = session.get("http://localhost:9999/v1/securities")
    securitiesList = []
    if resp.ok:
        securities = resp.json()
        for security in securities[1:]:
            securitiesList.append(security["ticker"])
        return securitiesList[:(len(securities)) // 2 + 1]
    raise ApiException("Authorization error. Please check API_KEY.")


def ticker_bid_ask(session, ticker):
    payload = {"ticker": ticker}
    print(ticker)
    resp = session.get("http://localhost:9999/v1/securities/book", params=payload)
    print(resp)
    if resp.ok:
        book = resp.json()
        return book["bids"][0]["price"], book["asks"][0]["price"]
    raise ApiException("Authorization error. Please check API_KEY.")


# change 1 month exp ticker to 2 month exp ticker
def get_month2_ticker(month1_ticker) -> str:
    return month1_ticker[:3] + '2' + month1_ticker[4:]


# return true when the short maturity bond can sell for a better price
# than the price you spend to buy a long maturity bonds
def call_ticker_compare(session, ticker) -> bool:
    bid_m1, ask_m1 = ticker_bid_ask(session, ticker)
    month2_ticker = get_month2_ticker(ticker)
    bid_m2, ask_m2 = ticker_bid_ask(session, month2_ticker)
    commission = 0.02 * 4
    bid_ask_spread = 0.04
    total_fee = commission + bid_ask_spread
    return bid_m1 > (ask_m2 + total_fee)


def get_limits(session):
    resp = session.get("http://localhost:9999/v1/limits")
    if resp.ok:
        limits = resp.json()
        return limits
    raise ApiException("Authorization error. Please check API_KEY.")


def get_securities(session):
    resp = session.get("http://localhost:9999/v1/securities")
    if resp.ok:
        securities = resp.json()
        return securities
    raise ApiException("Authorization error. Please check API_KEY.")


# get stock price for case 1 specifically
def get_stock_price(session) -> float:
    securities = get_securities(session)
    for security in securities:
        if security['type'] == 'STOCK':
            return security['last']


def get_time_in_years(session) -> float:
    case = get_case(session)
    period = case['period']
    tick = case['tick']
    if period == 2: tick += 300
    return (tick / 300) / 12


# get USD price in terms of CAD in question 3, action takes in 'bid'/'ask'
def get_USD(session, action):
    print("in get usd")
    payload = {"ticker": "USD"}
    resp = session.get("http://localhost:9999/v1/securities", params=payload)
    if resp.ok:
        USD = resp.json()
        print(USD)
        # assert(len(USD) == 1)
        USD = USD[0]

        return USD[action]
    raise ApiException("Authorization error. Please check API_KEY.")


def get_RITC(session, action):
    resp = session.get("http://localhost:9999/v1/securities?ticker=RITC")
    if resp.ok:
        RITC = resp.json()
        # assert(len(USD) == 1)
        RITC = RITC[0]
        return RITC[action]


def get_BULL(session, action):
    resp = session.get("http://localhost:9999/v1/securities?ticker=BULL")
    if resp.ok:
        BULL = resp.json()
        # assert(len(USD) == 1)
        BULL = BULL[0]
        return BULL[action]


def get_BEAR(session, action):
    resp = session.get("http://localhost:9999/v1/securities?ticker=BEAR")
    if resp.ok:
        BEAR = resp.json()
        # assert(len(USD) == 1)
        BEAR = BEAR[0]
        return BEAR[action]


def is_active(status):
    return status == 'ACTIVE'


def has_order(order):
    result = len(order) == 0 or order[0]['quantity'] == 0
    return result


################################################################

def get_case_name(case):
    print(case["name"])
    return case["name"]


def get_case_period(case):
    print(case["period"])
    return case["period"]


def get_case_tick(case):
    # print(case["tick"])
    return case["tick"]


def get_case_ticks_per_period(case):
    # print(case["ticks_per_period"])
    return case["ticks_per_period"]


def get_case_total_periods(case):
    # print(case["total_periods"])
    return case["total_periods"]


def get_case_status(case):
    # print(case["status"])
    return case["status"]


def is_enforce_trading_limits(case):
    print(case["is_enforce_trading_limits"])
    return case["is_enforce_trading_limits"]


def get_news(session, since=news_id):
    print("getting news")
    payload = {"since": since}
    resp = session.get("http://localhost:9999/v1/news", params=payload)
    print("news got successfully")
    if resp.ok:
        news = resp.json()
        print(news)
        for elem in news:
            news_id = elem["news_id"]
            result = ""
            result += "ticker: "
            result += elem["ticker"]
            result += "\n"
            result += elem["headline"]
            result += "\n"
            result += elem["body"]
        return
    raise ApiException("Authorization error. Please check API_KEY.")


def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_case_tick(s)
        print(tick)
        while tick > 5 and tick < 295 and not shutdown:
            tick = get_case_tick(s)
            print(tick)
            get_news(s, news_id)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()


def get_orders(session):
    resp = session.get("http://localhost:9999/v1/orders")
    if resp.ok:
        orders = resp.json()
        return orders
    raise ApiException("Authorization error. Please check API_KEY.")


def get_tenders(session):
    resp = session.get("http://localhost:9999/v1/tenders")
    if resp.ok:
        tenders = resp.json()
        return tenders
    raise ApiException("Authorization error. Please check API_KEY.")


def get_time_in_years(session) -> float:
    days = 0
    case = get_case(session)
    period = case['period']
    tick = case['tick']
    if period == 2: tick += 300
    return (tick / 300) / 12


# get USD price in terms of CAD in question 3, action takes in 'bid'/'ask'

def is_active(status):
    return status == 'ACTIVE'


def no_order(order):
    result = len(order) == 0 or order[0]['quantity'] == 0
    return result


################################################################

def get_case_name(case):
    print(case["name"])
    return case["name"]


def get_case_period(case):
    print(case["period"])
    return case["period"]


def get_case_tick(case):
    # print(case["tick"])
    return case["tick"]


def get_case_ticks_per_period(case):
    # print(case["ticks_per_period"])
    return case["ticks_per_period"]


def get_case_total_periods(case):
    # print(case["total_periods"])
    return case["total_periods"]


def get_case_status(case):
    # print(case["status"])
    return case["status"]


def is_enforce_trading_limits(case):
    print(case["is_enforce_trading_limits"])
    return case["is_enforce_trading_limits"]


def get_news(session, since=news_id):
    print("getting news")
    payload = {"since": since}
    resp = session.get("http://localhost:9999/v1/news", params=payload)
    print("news got successfully")
    if resp.ok:
        news = resp.json()
        print(news)
        for elem in news:
            news_id = elem["news_id"]
            result = ""
            result += "ticker: "
            result += elem["ticker"]
            result += "\n"
            result += elem["headline"]
            result += "\n"
            result += elem["body"]
        return
    raise ApiException("Authorization error. Please check API_KEY.")


def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_case_tick(s)
        print(tick)
        while tick > 5 and tick < 295 and not shutdown:
            tick = get_case_tick(s)
            print(tick)
            get_news(s, news_id)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
