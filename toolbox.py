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
API_KEY = {"X-API-Key": "KN0P68A7"}
shutdown = False
news_id = 0


def get_case(session):
    print("getting current status")
    resp = session.get("http://localhost:9999/v1/case")
    print("current status got successfully")
    if resp.ok:
        case = resp.json()
        print(case)
        return case
    raise ApiException("Authorization error. Please check API_KEY.")


def get_case_name(case):
    print(case["name"])
    return case["name"]


def get_case_period(case):
    print(case["period"])
    return case["period"]


def get_case_tick(case):
    print(case["tick"])
    return case["tick"]


def get_case_ticks_per_period(case):
    print(case["ticks_per_period"])
    return case["ticks_per_period"]


def get_case_total_periods(case):
    print(case["total_periods"])
    return case["total_periods"]


def get_case_status(case):
    print(case["status"])
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
