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
API_KEY = {'X-API-Key': 'KN0P68A7'}
shutdown = False


def get_tick(session):
    print('getting tick')
    resp = session.get('http://localhost:9999/v1/case')
    print('tick got successfully')
    if resp.ok:
        case = resp.json()
        print(case)
        return case['tick']
    raise ApiException('Authorization error. Please check API_KEY.')


def get_news(session):
    print("getting news")
    resp = session.get('http://localhost:9999/v1/news')
    print("news got successfully")
    if resp.ok:
        news = resp.json()
        print(news)
        return
    raise ApiException('Authorization error. Please check API_KEY.')


def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        print(tick)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
