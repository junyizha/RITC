import numpy as np
import pandas as pd
import scipy as sc
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

"""
Option Pricing Model:
Sigma: volatility
S: spot price of underlying
K: strike price
r: risk-free rate
t: time to expiry
"""


# the following code is adapted from Arjun Rohlfing-Das's Github page
def d(sigma, S, K, r, t):
    d1 = 1 / (sigma * np.sqrt(t)) * (np.log(S / K) + (r + sigma ** 2 / 2) * t)
    d2 = d1 - sigma * np.sqrt(t)
    return d1, d2


def call_price(sigma, S, K, r, t, d1, d2):
    C = np.norm.cdf(d1) * S - np.norm.cdf(d2) * K * np.exp(-r * t)
    return C


def put_price(sigma, S, K, r, t, d1, d2):
    P = -np.norm.cdf(-d1) * S + np.norm.cdf(-d2) * K * np.exp(-r * t)
    return P


def vega(sigma, S, K, r, t):
    d1, d2 = d(sigma, S, K, r, t)
    v = S * np.norm.pdf(d1) * np.sqrt(t)
    return v


def delta(d_1, contract_type):
    if contract_type == 'C':
        return np.norm.cdf(d_1)
    if contract_type == 'P':
        return -np.norm.cdf(-d_1)


def gamma(d2, S, K, sigma, r, t):
    return (K * np.exp(-r * t) * (np.norm.pdf(d2) / (S ** 2 * sigma * np.sqrt(t))))


def theta(d1, d2, S, K, sigma, r, t, contract_type):
    if contract_type == 'C':
        theta = -S * sigma * np.norm.pdf(d1) / (2 * np.sqrt(t)) - r * K * np.exp(-r * t) * np.norm.cdf(d2)
    if contract_type == 'P':
        theta = -S * sigma * np.norm.pdf(-d1) / (2 * np.sqrt(t)) + r * K * np.exp(-r * t) * np.norm.cdf(-d2)
    return theta


def implied_vol(sigma, S, K, r, t, bs_price, price):
    val = bs_price - price
    veg = vega(sigma, S, K, r, t)
    vol = -val / veg + sigma
    return vol


def get_tick(session):
    print('getting tick')
    resp = session.get('http://localhost:9999/v1/case')
    print('here')
    if resp.ok:
        case = resp.json()
        print(case)
        return case['tick']
    raise ApiException('Please check API_KEY')


def get_news(session):
    print("getting news")
    resp = session.get('http://localhost:9999/v1/news')
    print("news got sucessfully")
    if resp.ok:
        news = resp.json()
        print(news)
        return
    raise ApiException('Please check API_KEY')


def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)
        print(tick)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
