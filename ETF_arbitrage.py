'''
implementation 
0.extract price about USD, RITC, BULL, BEAR each tick

1. each tick
assure that they are either 

USD * RITC > BULL + BEAR 1*

or 

USD * RITC < BULL + BEAR 2*

    at case 1*
    SELL RITC + convert the gain to CAD *BID
    BUY BULL + BEAR *ASK


    at case 2*
    SELL BULL + BEAR convert to USD *BID
    BUY RITC *ASK

record such portfolio into a dataframe

2. each tick
check existing arbitrage portfolios

assure that we have

USD * RITC == BULL + BEAR

    at case 1* 
    SELL existing BULL + BEAR
    BUY RITC convert to CAD

    at case 2* 
    SELL existing RITC convert to CAD
    BUY BULL + BEAR
'''
import requests
import toolbox as tb
from ma_try import *
import pandas as pd


def get_last(session, ticker):
    s = "http://localhost:9999/v1/securities?ticker=" + ticker
    resp = session.get(s)
    if resp.ok:
        securities = resp.json()
        return securities[0]["last"]
    raise ApiException("Authorization error. Please check API_KEY.")


def main():
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = tb.get_case_tick(tb.get_case(s))
        print(tick)
        arbitrage_portfolio = dict()
        arbitrage_portfolio['RITC'] = 0
        arbitrage_portfolio['BULL'] = 0
        arbitrage_portfolio['BEAR'] = 0
        epsilon = 0.01
        threshold = 1.0
        caseOne = False
        caseTwo = False
        bought = False
        while tick > 5 and tick < 295:
            tick = tb.get_case_tick(tb.get_case(s))
            print(tick)
            USD_bid = tb.get_USD(s, 'bid')
            RITC_bid = tb.get_RITC(s, 'bid')
            BULL_bid = tb.get_BULL(s, 'bid')
            BEAR_bid = tb.get_BEAR(s, 'bid')
            USD_ask = tb.get_USD(s, 'ask')
            RITC_ask = tb.get_RITC(s, 'ask')
            BULL_ask = tb.get_BULL(s, 'ask')
            BEAR_ask = tb.get_BEAR(s, 'ask')
            if USD_bid * RITC_bid > BULL_ask + BEAR_ask + threshold and not bought:
                print(place_order(s, 'RITC', 'MARKET', 100, 'SELL'))
                print(place_order(s, 'BULL', 'MARKET', 100, 'BUY'))
                print(place_order(s, 'BEAR', 'MARKET', 100, 'BUY'))
                arbitrage_portfolio['RITC'] -= 100
                arbitrage_portfolio['BULL'] += 100
                arbitrage_portfolio['BEAR'] += 100
                caseOne = True
                bought = True
            elif USD_ask * RITC_ask < BULL_bid + BEAR_bid + threshold and not bought:
                place_order(s, 'RITC', 'MARKET', 100, 'BUY')
                place_order(s, 'BULL', 'MARKET', 100, 'SELL')
                place_order(s, 'BEAR', 'MARKET', 100, 'SELL')
                arbitrage_portfolio['RITC'] += 100
                arbitrage_portfolio['BULL'] -= 100
                arbitrage_portfolio['BEAR'] -= 100
                caseTwo = True
                bought = True
            while abs(get_last(s, 'USD') * get_last(s, 'RITC') - get_last(s, "BULL") - get_last(s, "BEAR")) > epsilon:
                pass

            assert (abs(get_last(s, 'USD') * get_last(s, 'RITC') - get_last(s, "BULL") - get_last(s, "BEAR")) <= epsilon)
            if caseOne and bought:
                place_order(s, 'BULL', 'MARKET', 100, 'SELL')
                place_order(s, 'BEAR', 'MARKET', 100, 'SELL')
                place_order(s, 'RITC', 'MARKET', 100, 'BUY')
            elif caseTwo and bought:
                place_order(s, 'RITC', 'MARKET', 100, 'SELL')
                place_order(s, 'BULL', 'MARKET', 100, 'BUY')
                place_order(s, 'BEAR', 'MARKET', 100, 'BUY')
            bought = False
            caseOne = False
            caseTwo = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
