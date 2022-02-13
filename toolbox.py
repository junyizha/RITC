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
tick = 0


def get_case(session):
    # print("getting current status")
    resp = session.get("http://localhost:9999/v1/case")
    # print("current status got successfully")
    if resp.ok:
        case = resp.json()
        #print(case)
        return case
    raise ApiException("Authorization error. Please check API_KEY.")


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


def get_news(session):
    global news_id
    # print("getting news with news_id", news_id)
    payload = {"since": news_id}
    resp = session.get("http://localhost:9999/v1/news", params=payload)
    # print("news got successfully")
    if resp.ok:
        news = resp.json()
        if len(news) == 0:
            return
        news_id = news[0]["news_id"]
        result = ""
        for elem in news:
            result += "ticker: "
            result += elem["ticker"]
            result += "\n"
            result += elem["headline"]
            result += "\n"
            result += elem["body"]
        return result
    raise ApiException("Authorization error. Please check API_KEY.")


def main():
    global tick
    with requests.Session() as s:
        s.headers.update(API_KEY)
        case = get_case(s)
        current_tick = get_case_tick(case)
        if current_tick != tick:
            print("current time: ", tick)
        while 0 < tick < 300 and not shutdown:
            case = get_case(s)
            current_tick = get_case_tick(case)
            if current_tick != tick:
                print("current time: ", tick)
            current_news = get_news(s)
            if current_news is not None:
                print(get_news(s))


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGUSR1, main)
    with requests.Session() as s:
        s.headers.update(API_KEY)
        while True:
            case = get_case(s)
            if get_case_status(case) == "ACTIVE":
                signal.raise_signal(signal.SIGUSR1)
