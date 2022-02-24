"""
Goal: Implement double moving average algorithm

Things to do:
   calc_history_atr
   sell
   buy
   cross
   calc_position
   stop_loss
"""
import signal
import requests
from time import sleep
import toolbox as tb
# need to be imported
import pandas as pd
import talib as tl
import numpy as np
import seaborn as sns

class ApiException(Exception):
    pass

def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

# port 9999 API KEY: UJM3CFTD
API_KEY = {"X-API-Key": "UJM3CFTD"}
shutdown = False
news_id = 0

################################################################
# 考虑买卖单的limit order
# 抓往期数据的时候要查到底有没有那么多数据

# Global Variables
# 两次处理交易逻辑的窗口大小
TRADE_BAR_DURATION = 15
LONG_MEAN = 30
SHORT_MEAN = 5
POSITION_SIGMA = 3
RISK_LIMIT = 0.1
# 跟踪止损的ATR倍数，即买入后，从最高价回撤该倍数的ATR后止损
TRAILING_STOP_LOSS_ATR = 4
# 计算ATR时的窗口大小
ATR_WINDOW = 20
# initial number
bar_number = 0
cache_data = dict()

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

# get tickers to trade
def get_tickers(session)->list:
    return ["BULL", "BEAR"]

def get_history(session, ticker):
    s = "http://localhost:9999/v1/securities/history?ticker="+ticker
    resp = session.get(s)
    if resp.ok:
        history = resp.json()
        return history
    raise ApiException("Authorization error. Please check API_KEY.")

def get_period_price(session, ticker:str, count:int, type:str)->list:
    history = get_history(session, ticker)
    price_list = []
    # testing
    #print(history)
    for i in range(0, count):
        price_list.insert(0, (history[i][type]))
    return price_list

def calc_history_atr(session, ticker, timeperiod=14):
    case = tb.get_case(session)
    high_price = get_period_price(session, ticker, timeperiod, type="high")
    low_price = get_period_price(session, ticker, timeperiod, type="low")
    close_price = get_period_price(session, ticker, timeperiod, type="close")
    return tl.ATR(np.array(high_price), np.array(low_price), np.array(close_price), timeperiod)[-1]

def get_positions(session, ticker):
    s = "http://localhost:9999/v1/securities?ticker="+ticker
    resp = session.get(s)
    if resp.ok:
        ticker = resp.json()
        return ticker[0]["position"]
    raise ApiException("Authorization error. Please check API_KEY.")

def get_current_price(session, ticker):
    s = "http://localhost:9999/v1/securities?ticker="+ticker
    resp = session.get(s)
    if resp.ok:
        securities = resp.json()
        return securities[0]["last"]
    raise ApiException("Authorization error. Please check API_KEY.")

"""
def stop_loss(session):
    '''
    跟踪止损
    '''
    limit = tb.get_limits(session)
    for ticker in get_tickers(session):
        position = get_positions(session, ticker)
        gross_prev = limit[1]["gross"]
        # 如果是多仓, 那么如果止损就要卖出
        if position > 0:
            current_price = get_current_price(session, ticker)
            # 获取持仓期间最高价
            high_price = cache_data[ticker]['high_price']
            atr = cache_data[ticker]['atr']
            if current_price <= high_price - atr * TRAILING_STOP_LOSS_ATR:
                order = place_order(session, ticker, order_type="MARKET", quantity=position, action="SELL")
                #filled = order[0]["quantity_filled"]
                #gross_after = limit[1]["gross"]
                #print(f'"交易 卖出 止损",{ticker},"卖出数量",{filled}, "交易金额",{gross_after-gross_prev},"剩余资金",{gross_after}')
        if position < 0:
            current_price = get_current_price(session, ticker)
            # 获取持仓期间最高价
            low_price = cache_data[ticker]['low_price']
            atr = cache_data[ticker]['atr']
            if current_price >= low_price + atr * TRAILING_STOP_LOSS_ATR:
                order = place_order(session, ticker, order_type="MARKET", quantity=position, action="BUY")
                #filled = order[0]["quantity_filled"]
                #gross_after = limit[1]["gross"]
                #print(f'"交易 买入 止损",{ticker},买入数量",{filled}, "交易金额",{gross_after-gross_prev},"剩余资金",{gross_after}')
"""

# 判断短时均线和长时均线的关系。
def cross(session, short_mean:list, long_mean:list, close_data:list)->bool:
    delta = short_mean[-3:] - long_mean[-3:]
    case = tb.get_case(session)
    tick = case["tick"]
    if (delta[-1] > 0) and ((delta[-2] < 0) or ((delta[-2] == 0) and (delta[-3] < 0))):
        print(f'tick = {tick}\n')
        print(f'close_data = {close_data[-33:]}\n')
        print(f'Buy Order\n')
        print(f'short_mean = {short_mean}\n')
        print(f'long_mean = {long_mean}\n')
        print(f'delta = {delta}\n\n')
        return 1
    elif (delta[-1] < 0) and ((delta[-2] > 0) or ((delta[-2] == 0) and (delta[-3] > 0))):
        print(f'tick = {tick}\n')
        print(f'close_data = {close_data[-33:]}\n')
        print(f'Sell Order\n')
        print(f'short_mean = {short_mean}\n')
        print(f'long_mean = {long_mean}\n')
        print(f'delta = {delta}\n\n')
        return -1
    return 0

def place_order(session, ticker, order_type, quantity, action):
    # 1. 算quantity的时候考虑到gross_limit和net_limit
    # this is ETF
    if order_type == "MARKET":
        log = session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 
        'type':order_type, 'quantity': quantity, 'action': action})
    else:
        log = session.post('http://localhost:9999/v1/orders', params={'ticker': ticker, 
        'type':order_type, 'quantity': quantity, 'action': action})
    return log
"""
def calc_position(session, ticker, action):
    '''
    计算建仓头寸

    Args:
        context 上下文
        code 要计算的标的的代码
    Returns:
        计算得到的头寸，单位 股数
    '''
    # 计算 risk_adjust_factor 用到的sigma的窗口大小
    RISK_WINDOW = 60
    # 计算 risk_adjust_factor 用到的两个sigma间隔大小
    RISK_DIFF = 30
    # 计算 sigma 的窗口大小
    SIGMA_WINDOW = 60

    # 计算头寸需要用到的数据的数量
    count = RISK_WINDOW + RISK_DIFF * 2
    count = max(SIGMA_WINDOW,count)

    h_array = get_period_price(session, ticker, count, type="high")
    l_array = get_period_price(session, ticker, count, type="low")
    c_array = get_period_price(session, ticker, count, type="close")
    
    # 数据转换
    value_array = []
    # 取平均价格
    for i in range(count):
        value_array.append((h_array[i] + l_array[i] + c_array[i] * 2) / 4)

    # 取三个窗口的sigma
    first_sigma = np.std(value_array[-RISK_WINDOW-(RISK_DIFF*2):-(RISK_DIFF*2)])    # -120:-60
    center_sigma = np.std(value_array[-RISK_WINDOW-(RISK_DIFF*1):-(RISK_DIFF*1)])    #  -90:-30
    last_sigma = np.std(value_array[-RISK_WINDOW:])                  #  -60:
    sigma = np.std(value_array[-SIGMA_WINDOW:])

    # 根据往期的波动率取sigma
    risk_adjust_factor = 0
    if last_sigma > center_sigma :
        risk_adjust_factor = 0.5
    elif last_sigma < center_sigma and last_sigma > first_sigma:
        risk_adjust_factor = 1.0
    elif last_sigma < center_sigma and last_sigma < first_sigma:
        risk_adjust_factor = 1.5

    limit = tb.get_limits(session)
    # 最大可以亏损 (total asset * RISK_LIMIT * risk_adjust_factor)
    return int(limit[1]["gross_limit"] * RISK_LIMIT * risk_adjust_factor / ((POSITION_SIGMA * sigma) * 100))  * 100
"""

def plotting(session, ticker):
    case = tb.get_case(session)
    tick = case["tick"]
    # get all data to draw line
    if (tick >= 40):
        hist_data = get_period_price(session, ticker=ticker, count=tick-1, type="close")
        long_mean = moving_average(hist_data, LONG_MEAN)
        short_mean = moving_average(hist_data, SHORT_MEAN)
        length = min(len(short_mean), len(long_mean), len(hist_data))
        print_hist_data = hist_data[-length:]
        #min_price = int(min(print_hist_data))-2
        #max_price = int(max(print_hist_data))+2
        print_long_mean = long_mean[-length:]
        print_short_mean = short_mean[-length:]
    d = {'hist_data': print_hist_data, 'long_mean': print_long_mean, 'short_mean': print_short_mean}
    df = pd.DataFrame(data=d)
    sns.lineplot(data=df)
    sleep(10)


def sell(session):
    '''
    卖出逻辑。
    当标的触发短时均线下穿长时均线时，卖出标的
    '''
    tickers = get_tickers(session)
    for ticker in tickers:
        # 计算均线交叉需要最新3个均线值。所以这里需要+3
        count = max(LONG_MEAN,SHORT_MEAN) + 3
        # 拿到count个period的数据
        close_data = np.array(get_period_price(session, ticker, count, type="close"))
        # moving average
        long_mean = moving_average(close_data, LONG_MEAN)
        short_mean = moving_average(close_data, SHORT_MEAN)
        # 短时均线下穿长时均线时买入
        if (cross(session, short_mean,long_mean,close_data) < 0):
            """
            limit = tb.get_limits(session)
            gross = limit[1][gross]
            net = limit[1][gross]
            gross_limit = limit[1][gross]
            net_limit = limit[1][gross]
            available_cash = net_limit - net
            """
            limit = tb.get_limits(session)
            gross_prev = limit[1]["gross"]
            #position_amount = calc_position(session, ticker, action="SELL")
            # 如果有多仓，先平仓再做空
            position = get_positions(session, ticker)
            if position > 0:
                place_order(session, ticker, order_type="MARKET", quantity=(position), action="SELL")
            # 再下单
            place_order(session, ticker, order_type="MARKET", quantity=1000, action="SELL")
            #filled = order[0]["quantity_filled"]
            #gross_after = limit[1]["gross"]
            #print(f'"交易 卖出 死叉",{ticker},"卖出数量",{filled}, "交易金额",{gross_after-gross_prev},"剩余资金",{gross_after}')
             
def buy(session):
    '''
    买入逻辑。
    当标的触发短时均线上穿长时均线时，买入标的
    '''
    tickers = get_tickers(session)
    for ticker in tickers:
        # 计算均线交叉需要最新3个均线值。所以这里需要+3
        count = max(LONG_MEAN,SHORT_MEAN) + 3
        # 拿到count个period的数据
        close_data = get_period_price(session, ticker, count, type="close")
        # moving average
        long_mean = moving_average(np.array(close_data), LONG_MEAN)
        short_mean = moving_average(np.array(close_data), SHORT_MEAN)
        # 短时均线下穿长时均线时买入
        if (cross(session,short_mean,long_mean,close_data) > 0):
            limit = tb.get_limits(session)
            """
            net = limit[1][gross]
            gross_limit = limit[1][gross]
            net_limit = limit[1][gross]
            available_cash = net_limit - net
            """
            gross_prev = limit[1]["gross"]
            #position_amount = calc_position(session, ticker, action="BUY")
            # 如果有做空，平仓后再做多
            position = get_positions(session, ticker)
            if position < 0:
                place_order(session, ticker, order_type="MARKET", quantity=(-position), action="BUY")
            # 再下单
            place_order(session, ticker, order_type="MARKET", quantity=1000, action="BUY")
            #filled = order[0]["quantity_filled"]
            #gross_after = limit[1]["gross"]
            #print(f'"交易 买入 金叉",{ticker},"买出数量",{filled}, "交易金额",{gross_after-gross_prev},"剩余资金",{gross_after}')

def main():
    with requests.Session() as session:
        global bar_number
        global cache_data
        #a dict of arbitrage portfolio, 
        # elem in format (month1name, month2name):orderquantit
        session.headers.update(API_KEY)
        case = tb.get_case(session)
        tick = case["tick"]
        # 更新持仓股票的最高价
        while (tick > LONG_MEAN+5) and (tick < 600) and not shutdown:
            #for ticker in get_tickers(session):
                #position = get_positions(session, ticker)
                #high_price = get_period_price(session, ticker, count=1, type="high")
                #if ticker not in cache_data.keys():
                #    cache_data[ticker] = dict()
                #cache_data[ticker]['high_price'] = high_price
                #low_price = get_period_price(session, ticker, count=1, type="low")
                #if ticker not in cache_data.keys():
                #    cache_data[ticker] = dict()
                #cache_data[ticker]['low_price'] = low_price
                # 更新标的的ATR数据
                #atr = calc_history_atr(session, ticker=ticker, timeperiod=ATR_WINDOW)
                #if ticker not in cache_data.keys():
                #    cache_data[ticker] = dict()
                #cache_data[ticker]['atr'] = atr
                #止损
                #stop_loss(session)
                #if bar_number % TRADE_BAR_DURATION == 0:
            sell(session)
            buy(session)
            #bar_number = (bar_number + 1 ) % TRADE_BAR_DURATION
            sleep(1)
        plotting(session, "BULL")
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    while(True):
        main()
    
