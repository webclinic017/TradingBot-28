import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from sqlite3 import OperationalError
import alpaca_trade_api as api


class trade_idea:
    def __init__(self, symbol, time_frame, position, time_posted, user):
        self.symbol = symbol
        self.time_frame = time_frame
        self.position = position
        self.time_posted = time_posted
        self.user = user


def alpaca_connect():
    API_KEY = 'PKQA6MM20L2CQZKAOAHW'
    API_SECRET = '4AJeSo8hcSqHa2TNwJv9IS8efb5PNDxHUju3UJjH'
    BASE_URL = "https://paper-api.alpaca.markets"

    alpaca = api.REST(API_KEY, API_SECRET, BASE_URL)
    return alpaca


def get_trade_ideas_db():
    con = sqlite3.connect('TradingBotDatabase.db')
    cur = con.cursor()
    trade_ideas = []
    for row in cur.execute(f"SELECT * FROM trade_ideas;"):
        trade_ideas.append(trade_idea(row[0], row[1], row[2], row[3], row[4]))
    return trade_ideas


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_trade_idea(conn, idea):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    sql = ''' INSERT OR IGNORE INTO trade_ideas(symbol,time_frame,position,time_posted,user)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, idea)
    conn.commit()
    return cur.lastrowid


def create_new_table():
    database = r"TradingBotDatabase.db"

    # create a database connection
    conn = create_connection(database)
    sql_create_trade_ideas_table = """ CREATE TABLE IF NOT EXISTS stock_data (
                                        symbol text NOT NULL,
                                        timestamp timestamp NOT NULL,
                                        open float NOT NULL,
                                        high float NOT NULL,
                                        low float NOT NULL,
                                        close float NOT NULL,
                                        volumne integer NOT NULL,
                                        PRIMARY KEY(symbol)
                                    ); """
    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_trade_ideas_table)
    else:
        print("Error! cannot create the database connection.")


def add_trade_ideas(trade_ideas):
    database = r"TradingBotDatabase.db"

    # create a database connection
    conn = create_connection(database)

    # create tables
    #     if conn is not None:
    #         # create projects table
    #         create_table(conn, sql_create_trade_ideas_table)
    #     else:
    #         print("Error! cannot create the database connection.")

    with conn:
        # tasks
        for i in trade_ideas:
            print(i)
            trade_idea = (i.symbol, i.time_frame, i.position, i.time_posted, i.user)
            create_trade_idea(conn, trade_idea)

        # create tasks


def add_stock_data(stock, symbol):
    database = r"TradingBotDatabase.db"

    # create a database connection
    conn = create_connection(database)

    with conn:
        # tasks
        for i in stock:
            print(i)
            trade_idea = (i.symbol, i.time_frame, i.position, i.time_posted, i.user)
            create_trade_idea(conn, trade_idea)

        # create tasks


def get_trade_ideas_from_tradingview(begin_page, end_page):
    tradingview_trade_ideas = []
    for i in range(begin_page, end_page):
        print(i)
        tradingview_trade_ideas.extend(__store_all_data(
            "https://www.tradingview.com/markets/stocks-usa/ideas/page-%d/" % i))
    print(len(tradingview_trade_ideas))
    return tradingview_trade_ideas


def __store_all_data(URL):
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
        if (symbol != None and time_frame != None and position != None and time_posted != None and user != None):
            trade_ideas.append(
                trade_idea(symbol.text, time_frame.text, position.text, time_posted['data-timestamp'], user.text))
    return trade_ideas


def __calculate_profit(stock, profit_exit, loss_exit):
    buy = 100
    initial_price = stock['open'][0]
    exit1 = profit_exit
    exit2 = loss_exit
    for i in stock['open']:
        if i / initial_price > exit1:
            print("initial_price: ", initial_price, "current price: ", i)
            return (buy * (i / initial_price)) - buy
        if i / initial_price < exit2:
            print("initial_price: ", initial_price, "current price: ", i)
            return (buy * (i / initial_price)) - buy
    return 0


def calculate_total_profit(trade_ideas, profit_exit_margin, exit_trade_margin, alpaca, good_users=None,
                                      min_total_profit=10, min_trade_amount=10):
    total_profit = 0
    users = {}
    if good_users is not None:
        trade_ideas = filter_trade_ideas_good_users(good_users, trade_ideas, min_total_profit, min_trade_amount)

    for idea in trade_ideas:
        stock_data = get_stock_data(idea, alpaca)
        if len(stock_data) < 100:
            continue
        profit = __calculate_short_long_profit(exit_trade_margin, idea, profit_exit_margin, stock_data)
        total_profit += profit
        if idea.user not in users:
            users[idea.user] = [0, 0]
        users[idea.user][0] += profit
        users[idea.user][1] += 1
        print(idea.symbol, idea.time_frame, idea.position, profit)
    print("TOTAL PROFIT: ", total_profit)
    return users


def performance_sorted_users(users):
    users_df = pd.DataFrame.from_dict(users, orient='index').sort_values(0, ascending=False)
    users_df = users_df.rename(columns={0: "total profit", 1: "trade count"})
    return users_df


def filter_trade_ideas_good_users(users, trade_ideas, min_total_profit=10, min_trade_amount=10):
    users_df = performance_sorted_users(users)
    good_users_df = users_df.loc[
        (users_df['total profit'] >= min_total_profit) & (users_df['trade count'] >= min_trade_amount)]
    good_users_list = good_users_df.index.tolist()
    filtered_trade_ideas = filter(lambda idea: idea.user in good_users_list, trade_ideas)
    return filtered_trade_ideas


def __calculate_short_long_profit(exit_trade_margin, idea, profit_exit_margin, stock_data):
    if idea.position == "Long":
        profit = __calculate_profit(stock_data, 1 + profit_exit_margin, 1 - exit_trade_margin)
    elif idea.position == "Short":
        profit = -__calculate_profit(stock_data, 1 + exit_trade_margin, 1 - profit_exit_margin)
    else:
        profit = 0
    return profit


def get_stock_data(idea, alpaca):
    try:
        stock = __get_stock_db(idea.symbol, idea.time_posted, time.time() - 86400)
    except OperationalError:
        stock = __get_stock_alpaca(idea.symbol, idea.time_posted, time.time() - 86400, alpaca)
    return stock


def __get_stock_db(stock_symbol, date_begin, date_end):
    con = sqlite3.connect('TradingBotDatabase.db')
    cur = con.cursor()
    date_begin = datetime.fromtimestamp(int(float(date_begin))).strftime("%Y-%m-%d %H:%M:%S")
    date_end = datetime.fromtimestamp(int(float(date_end))).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(f"""SELECT *     
        FROM {stock_symbol} 
        WHERE timestamp > '{date_begin}'
        AND timestamp < '{date_end}';""")
    stock = pd.DataFrame(cur.fetchall()).set_index(0)
    stock.rename(
        columns={0: 'Timestamp', 1: 'open', 2: 'High', 3: 'Low', 4: 'Close', 5: 'Volume', 6: 'Trade Count', 7: 'VWAP'},
        inplace=True)
    return stock


def __get_stock_alpaca(stock_symbol, date_begin, date_end, alpaca, timeframe="1Min"):
    date_begin = datetime.fromtimestamp(int(float(date_begin))).strftime("%Y-%m-%d")
    date_end = datetime.fromtimestamp(int(float(date_end))).strftime("%Y-%m-%d")
    conn = create_connection('TradingBotDatabase.db')
    stock = alpaca.get_bars(stock_symbol, timeframe, date_begin, date_end).df
    stock.to_sql(stock_symbol, conn, if_exists='append')
    print("stored in db")
    return stock


def print_trade_ideas(trade_ideas):
    for i in trade_ideas:
        print(i.symbol, i.time_frame, i.position, i.time_posted, i.user)


if __name__ == '__main__':
    API_KEY = 'PKQA6MM20L2CQZKAOAHW'
    API_SECRET = '4AJeSo8hcSqHa2TNwJv9IS8efb5PNDxHUju3UJjH'
    BASE_URL = "https://paper-api.alpaca.markets"

    alpaca = api.REST(API_KEY, API_SECRET, BASE_URL)
    # trade_ideas = get_trade_ideas_db()
    # users = calculate_total_profit(trade_ideas[:100], 0.010, 0.005)
