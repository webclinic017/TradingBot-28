import finnhub
import pandas as pd
import datetime
import requests
from bs4 import BeautifulSoup
import re
import time

class trade_idea:
    def __init__(self, symbol, time_frame, position, time_posted, user):
        self.symbol = symbol
        self.time_frame = time_frame
        self.position = position
        self.time_posted = time_posted
        self.user = user

def get_trade_ideas(begin_page, end_page):
    trade_ideas = []
    for i in range(begin_page, end_page):
        trade_ideas.extend(store_all_data("https://www.tradingview.com/markets/stocks-usa/ideas/page-%d/" % i))
    print(len(trade_ideas))
    return trade_ideas

def store_all_data(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    data = soup.find_all("div", class_="tv-widget-idea js-userlink-popup-anchor")
    trade_ideas = []
    print(len(data))
    for i in data:
        symbol = i.find('a', class_="tv-widget-idea__symbol apply-overflow-tooltip")
        time_frame = i.find_all('span', class_="tv-widget-idea__timeframe")[1]
        position = i.find('span', class_="content-yHuWj4ze badge-idea-content-Naj79Gc7")
        time_posted = i.find('span', class_="tv-card-stats__time")
        user = i.find('span', class_="tv-card-user-info__name")
        if(symbol != None and time_frame != None and position != None and time_posted != None and user != None):
            trade_ideas.append(trade_idea(symbol.text, time_frame.text, position.text, time_posted['data-timestamp'], user.text))          
    return trade_ideas

def calculate_profit(stock, profit_exit, loss_exit):
    buy = 100
    initial_price = stock['Open'][0]
    exit1 = profit_exit
    exit2 = loss_exit
    for i in stock['Open']:
        if i / initial_price > exit1:
            print("initial_price: ", initial_price, "current price: ", i)
            return (buy * (i / initial_price)) - buy
        if i / initial_price < exit2:
            print("initial_price: ", initial_price, "current price: ", i)
            return (buy * (i / initial_price)) - buy
    return 0

def calculate_total_long_profit(trade_ideas, profit_exit_margin, exit_trade_margin):
    sum = 0
    for i in trade_ideas:
        stock = get_stock(i.symbol, i.time_posted, time.time())
        if i.position == "Long":
            profit = calculate_profit(stock, 1+profit_exit_margin, 1-exit_trade_margin)
            sum += profit
            print(i.symbol, i.time_frame, i.position, profit)
            
        if i.position == "Short":
            profit = -calculate_profit(stock, 1+exit_trade_margin, 1-profit_exit_margin)
            sum += profit
            print(i.symbol, i.time_frame, i.position, profit)
    print(sum)

def get_stock(stock_symbol, date_begin, date_end):
    data = finnhub_client.stock_candles(stock_symbol, 'D', int(float(date_begin)), int(float(date_end)))
    df = pd.DataFrame(data)
    df['t'] = df['t'].apply(lambda x: datetime.datetime.fromtimestamp(x))
    stock = df[['t','o','h','l','c','v']].set_index('t')
    stock.rename(columns={'o': 'Open', 'h': 'High', 'l':'Low','c':'Close','v':'Volume'}, inplace=True)
    return stock        

def print_trade_ideas():
    for i in trade_ideas:
        print(i.symbol, i.time_frame, i.position, i.time_posted, i.user)
        
        
if __name__ == '__main__':
    get_trade_ideas(200,201)
