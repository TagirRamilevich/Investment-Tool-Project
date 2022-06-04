# pip install pathlib
# pip install ruamel-yaml
# pip install yfinance
# pip install pytelegrambotapi


import telebot
import sqlite3
from sqlite3 import Error
from telebot import types
from datetime import date
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import dataframe_image as dfi


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

bot = telebot.TeleBot('')
connection = sqlite3.connect('dwh.db', check_same_thread=False)
today = date.today()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    username = message.from_user.username
    query = (f"""
                insert or ignore into user_info (user_id, user_first_name, user_last_name, user_username)
                values ({user_id}, '{user_name}', '{user_last_name}', '{username}');
             """)
    post_sql_query(query)
    markup = types.InlineKeyboardMarkup()
    button_a = types.InlineKeyboardButton('Новости', callback_data='News')
    button_b = types.InlineKeyboardButton('ISIN Number', callback_data='ISIN')
    button_c = types.InlineKeyboardButton('Дивиденды', callback_data='Dividends')
    button_d = types.InlineKeyboardButton('Ежедневные торги', callback_data='Trading')
    button_e = types.InlineKeyboardButton('Прогнозы аналитиков', callback_data='Recommendations')
    button_f = types.InlineKeyboardButton('Общие данные', callback_data='General_Information')
    button_g = types.InlineKeyboardButton('Финансы', callback_data='Financial_Information')
    button_h = types.InlineKeyboardButton('Котировки', callback_data='Plot')
    button_k = types.InlineKeyboardButton('Добавить бумагу', callback_data='Add_Share')
    button_l = types.InlineKeyboardButton('Удалить бумагу', callback_data='Delete_Share')
    button_m = types.InlineKeyboardButton('Показать портфель', callback_data='Show_Portfolio')
    markup.row(button_a, button_b)
    markup.row(button_c, button_d)
    markup.row(button_g, button_f)
    markup.row(button_e, button_h)
    markup.row(button_k, button_l)
    markup.row(button_m)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


def post_sql_query(sql_query):
    with sqlite3.connect('dwh.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql_query)
        except Error:
            pass
        result = cursor.fetchall()
        return result


def create_table_user_info():
    query = ("""create table if not exists 'user_info' (
	                'id' INTEGER NOT NULL UNIQUE,
	                'user_id' TEXT NOT NULL UNIQUE,
	                'user_first_name' TEXT,
	                'user_last_name' TEXT,
	                'user_username' TEXT,
	                PRIMARY KEY('id' AUTOINCREMENT));
	         """)
    post_sql_query(query)


def create_table_user_portfolio():
    query = ("""create table if not exists 'user_portfolio' (
	            'transaction_id' INTEGER NOT NULL UNIQUE,
	            'user_id' INTEGER NOT NULL,
	            'ticker' TEXT NOT NULL,
	            'purchase_date'	TEXT NOT NULL,
	            'number_of_shares' INTEGER NOT NULL,
	            'price_per_share' NUMERIC NOT NULL,
	            'currency' TEXT NOT NULL,
	            'sum' TEXT,
	            PRIMARY KEY('transaction_id' AUTOINCREMENT));
	         """)
    post_sql_query(query)


create_table_user_info()
create_table_user_portfolio()


@bot.message_handler(commands=['del'])
def reg(message):
    user_id = message.from_user.id
    query = (f"""
                delete from user_info as ui
                where ui.user_id = {user_id};
             """)
    post_sql_query(query)
    bot.send_message(message.from_user.id, "Твои данные удалены из базы!")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "News":
        reply = bot.send_message(call.message.chat.id,
                                 'Новости какой компании тебя интересуют?')
        bot.send_message(call.message.chat.id,
                         '_Введи название или тикер компании_',
                         parse_mode="Markdown")
        bot.register_next_step_handler(reply, ticker_news)
    elif call.data == "ISIN":
        reply = bot.send_message(call.message.chat.id,
                                 'ISIN номер тикера какой компании тебя интересует?')
        bot.register_next_step_handler(reply, ticker_isin)
    elif call.data == "Dividends":
        reply = bot.send_message(call.message.chat.id,
                                 'С какого дня тебя интересует история выплаты дивидендов?')
        bot.send_message(call.message.chat.id,
                         '_Введи дату в формате YYYY-MM-DD_',
                         parse_mode="Markdown")
        bot.register_next_step_handler(reply, get_start_date_dividends)
    elif call.data == "Trading":
        message = bot.send_message(call.message.chat.id,
                                   'С какого дня тебя интересует сводка?')
        bot.send_message(call.message.chat.id,
                         '_Введи дату в формате YYYY-MM-DD_',
                         parse_mode="Markdown")
        bot.register_next_step_handler(message, get_start_date_history)
    elif call.data == "Recommendations":
        message = bot.send_message(call.message.chat.id,
                                   'С какого дня тебя интересуют прогнозы аналитиков?')
        bot.send_message(call.message.chat.id,
                         '_Введи дату в формате YYYY-MM-DD_',
                         parse_mode="Markdown")
        bot.register_next_step_handler(message, get_start_date_recommendations)
    elif call.data == "General_Information":
        message = bot.send_message(call.message.chat.id,
                                   'Базовая информация о компании с каким тикером тебя интересует?')
        bot.register_next_step_handler(message, ticker_information_general)
    elif call.data == "Financial_Information":
        message = bot.send_message(call.message.chat.id,
                                   'Финансовые показатели компании с каким тикером тебя интересуют?')
        bot.register_next_step_handler(message, ticker_information_financial)
    elif call.data == "Plot":
        message = bot.send_message(call.message.chat.id,
                                   'С какого дня тебя интересуют котировки компании?')
        bot.send_message(call.message.chat.id,
                         '_Введи дату в формате YYYY-MM-DD_',
                         parse_mode="Markdown")
        bot.register_next_step_handler(message, get_start_date_plot)
    elif call.data == "Add_Share":
        message = bot.send_message(call.message.chat.id,
                                   'Какой тикер у этой акции?')
        bot.register_next_step_handler(message, get_share_ticker)
    elif call.data == "Delete_Share":
        message = bot.send_message(call.message.chat.id,
                                   'Какой тикер у этой акции?')
        bot.register_next_step_handler(message, get_share_ticker_del)
    elif call.data == "Show_Portfolio":
        message = bot.send_message(call.message.chat.id,
                                   f'Твой портфель на дату *{today.strftime("%d/%m/%Y")}*',
                                   parse_mode='Markdown')
        try:
            user_id = message.chat.id
            query = (f"""
                        select * 
                        from user_portfolio as up
                        where 1 = 1
                            and up.user_id = {user_id}
                    """)
            df_portfolio_aggregate = pd.read_sql(query, connection)
            df_portfolio_aggregate = df_portfolio_aggregate[
                ['ticker', 'currency', 'number_of_shares', 'sum']].groupby(
                ['ticker', 'currency']).sum()
            df_portfolio_aggregate['share_average'] = round(df_portfolio_aggregate['sum'] /
                                                            df_portfolio_aggregate['number_of_shares'], 2)
            df_portfolio_aggregate.reset_index(inplace=True)
            dfi.export(df_portfolio_aggregate, 'C:/Users/tkhayrutdinov/dataframe_portfolio_agg.png')
            photo = open(r'C:/Users/tkhayrutdinov/dataframe_portfolio_agg.png', 'rb')
            bot.send_photo(message.chat.id,
                           photo=photo)
        except NameError:
            reply = 'Ты не создал портфель.'
            bot.send_message(message.chat.id,
                             reply)
        except KeyError:
            reply = 'Ты не добавил бумаг в портфель.'
            bot.send_message(message.chat.id,
                             reply)


@bot.message_handler(content_types=['text', 'document', 'audio', 'photo'])
def get_text_messages(message):
    if message.text.lower() == "/start":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /start.")


def portfolio_df_astype(df_portfolio):
    df_portfolio['Ticker'] = df_portfolio['Ticker'].astype('string')
    df_portfolio['Purchase date'] = df_portfolio['Purchase date'].astype('datetime64[ns]')
    df_portfolio['Number of shares'] = df_portfolio['Number of shares'].astype('int64')
    df_portfolio['Price per share'] = df_portfolio['Price per share'].astype('float64')
    df_portfolio['Currency'] = df_portfolio['Currency'].astype('string')
    return df_portfolio


def portfolio_df_astype_sql(df_portfolio):
    df_portfolio['ticker'] = df_portfolio['ticker'].astype('string')
    df_portfolio['purchase_date'] = df_portfolio['purchase_date'].astype('datetime64[ns]')
    df_portfolio['number_of_shares'] = df_portfolio['number_of_shares'].astype('int64')
    df_portfolio['price_per_share'] = df_portfolio['price_per_share'].astype('float64')
    df_portfolio['currency'] = df_portfolio['currency'].astype('string')
    return df_portfolio


def get_share_ticker_del(message):
    global share_del_ticker
    share_del_ticker = message.text
    bot.send_message(message.from_user.id, 'Сколько акций ты продал?')
    bot.register_next_step_handler(message, get_share_qty_del)


def get_share_qty_del(message):
    global share_del_quantity
    share_del_quantity = message.text
    bot.send_message(message.from_user.id, 'Какова стоимость продажи 1 акции?')
    bot.register_next_step_handler(message, get_share_price_del)


def get_share_price_del(message):
    global share_del_price
    share_del_price = message.text
    bot.send_message(message.from_user.id, 'Какая валюта у этой акции?')
    bot.send_message(message.from_user.id,
                     '_Введи международный код валюты из 3 символов (usd, rub и т.д.)_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, portfolio_delete_share)


def portfolio_delete_share(message):
    global df_portfolio
    try:
        share_del_currency = message.text
        user_id = message.chat.id
        query_select = (f"""
                    select ticker, purchase_date, number_of_shares, price_per_share, currency, sum
                    from user_portfolio as up
                    where 1 = 1
                        and up.ticker = '{share_del_ticker.upper()}'
                        and up.currency = '{share_del_currency.upper()}'
                        and up.user_id = {user_id}
                """)
        df_portfolio_aggregate = pd.read_sql(query_select, connection)
        if int(df_portfolio_aggregate['number_of_shares']) >= int(share_del_quantity):
            query_delete = (f"""
                        delete from user_portfolio as up
                        where 1 = 1
                            and up.ticker = '{share_del_ticker.upper()}'
                            and up.currency = '{share_del_currency.upper()}'
                            and up.user_id = {user_id}
                    """)
            post_sql_query(query_delete)
            df_portfolio = pd.DataFrame(
                columns=['ticker', 'purchase_date', 'number_of_shares', 'price_per_share', 'currency'])
            portfolio_df_astype_sql(df_portfolio)
            df_portfolio_temp = pd.DataFrame({'ticker': share_del_ticker.upper(),
                                              'purchase_date': df_portfolio_aggregate['purchase_date'],
                                              'number_of_shares': int(df_portfolio_aggregate['number_of_shares']) - int(share_del_quantity),
                                              'price_per_share': (float(df_portfolio_aggregate['sum']) - float(df_portfolio_aggregate['price_per_share']) * int(share_del_quantity))
                                                                  / (int(df_portfolio_aggregate['number_of_shares']) - int(share_del_quantity)),
                                              'currency': df_portfolio_aggregate['currency']},
                                             index=[0])
            portfolio_df_astype_sql(df_portfolio_temp)
            df_portfolio = df_portfolio.append(df_portfolio_temp, ignore_index=True)
            df_portfolio['sum'] = df_portfolio['number_of_shares'] * df_portfolio['price_per_share']
            query_insert = (f"""
                        insert into user_portfolio (user_id, ticker, purchase_date, number_of_shares, price_per_share, currency, sum)
                        values ({user_id},
                                {df_portfolio['ticker'].values[0]},
                                {df_portfolio_aggregate['purchase_date'].values[0]},
                                {df_portfolio['number_of_shares'].values[0]},
                                {df_portfolio['price_per_share'].values[0]},
                                {df_portfolio['currency'].values[0]},
                                {df_portfolio['sum'].values[0]});
                     """)
            post_sql_query(query_insert)
            dfi.export(df_portfolio.tail(1), 'C:/Users/tkhayrutdinov/dataframe_portfolio.png')
            photo = open(r'C:/Users/tkhayrutdinov/dataframe_portfolio.png', 'rb')
            reply = 'Теперь данная акция выглядит так:'
            bot.send_message(message.from_user.id,
                             reply)
            bot.send_photo(message.from_user.id,
                           photo=photo)
        else:
            reply = 'Кажется, у тебя нет столько акций.'
            bot.send_message(message.chat.id,
                             reply)
    except ValueError:
        reply = 'Ты ввёл что-то неправильно.'
        bot.send_message(message.chat.id,
                         reply)
    except ZeroDivisionError:
        reply = 'Бумага успешно удалена!'
        bot.send_message(message.chat.id,
                         reply)
    except TypeError:
        reply = 'Кажется, у тебя нет такой акции. Проверь валюту.'
        bot.send_message(message.chat.id,
                         reply)


def get_share_ticker(message):
    global share_purchase_ticker
    share_purchase_ticker = message.text
    bot.send_message(message.from_user.id, 'Когда ты купил эту акцию?')
    bot.send_message(message.from_user.id,
                     '_Введи дату в формате YYYY-MM-DD_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, get_share_date)


def get_share_date(message):
    global share_purchase_date
    share_purchase_date = message.text
    bot.send_message(message.from_user.id, 'Сколько акций ты купил?')
    bot.register_next_step_handler(message, get_share_qty)


def get_share_qty(message):
    global share_purchase_quantity
    share_purchase_quantity = message.text
    bot.send_message(message.from_user.id, 'Какова стоимость 1 акции?')
    bot.register_next_step_handler(message, get_share_price)


def get_share_price(message):
    global share_purchase_price
    share_purchase_price = message.text
    bot.send_message(message.from_user.id, 'Какая валюта у этой акции?')
    bot.send_message(message.from_user.id,
                     '_Введи международный код валюты из 3 символов (usd, rub и т.д.)_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, portfolio_add_share)


def portfolio_add_share(message):
    global df_portfolio
    try:
        share_purchase_currency = message.text
        df_portfolio = pd.DataFrame(
            columns=['Ticker', 'Purchase date', 'Number of shares', 'Price per share', 'Currency'])
        portfolio_df_astype(df_portfolio)
        df_portfolio_temp = pd.DataFrame({'Ticker': share_purchase_ticker.upper(),
                                          'Purchase date': share_purchase_date,
                                          'Number of shares': share_purchase_quantity,
                                          'Price per share': share_purchase_price.replace(',', '.'),
                                          'Currency': share_purchase_currency.upper()},
                                         index=[0])
        portfolio_df_astype(df_portfolio_temp)
        df_portfolio = df_portfolio.append(df_portfolio_temp, ignore_index=True)
        df_portfolio['Sum'] = df_portfolio['Number of shares'] * df_portfolio['Price per share']
        user_id = message.from_user.id
        query = (f"""
                    insert into user_portfolio (user_id, ticker, purchase_date, number_of_shares, price_per_share, currency, sum)
                    values ({user_id}, '{share_purchase_ticker.upper()}', '{share_purchase_date}', {share_purchase_quantity}, 
                            {share_purchase_price}, '{share_purchase_currency.upper()}', {int(share_purchase_quantity) * float(share_purchase_price)});
                 """)
        post_sql_query(query)
        dfi.export(df_portfolio.tail(1), 'C:/Users/tkhayrutdinov/dataframe_portfolio.png')
        photo = open(r'C:/Users/tkhayrutdinov/dataframe_portfolio.png', 'rb')
        reply = 'Ты уверен, что ввёл всё правильно?' + '\n' + 'Напиши "да", если это так и "нет", если это не так.'
        bot.send_message(message.from_user.id,
                         reply)
        bot.send_photo(message.from_user.id,
                       photo=photo)
        bot.register_next_step_handler(message, portfolio_add_share_confirmation)
    except ValueError:
        reply = 'Ты ввёл что-то неправильно.'
        bot.send_message(message.chat.id,
                         reply)


def portfolio_add_share_confirmation(message):
    if message.text.lower() == 'да':
        reply = 'Акции успешно добавлены в портфель!'
        bot.send_message(message.from_user.id,
                         reply, reply_to_message_id=message.message_id)
    else:
        user_id = message.from_user.id
        query = (f"""
                    delete from user_portfolio as up
                    where 1 = 1
                        and up.transaction_id = (
                                                 select max(up.transaction_id)
                                                 from user_portfolio as up
                                                 where 1 = 1
                                                    and up.user_id = {user_id}                        
                                                )
                 """)
        post_sql_query(query)
        df_portfolio.drop(df_portfolio.tail(1).index, inplace=True)
        reply = 'Акции не были добавлены в портфель.'
        bot.send_message(message.from_user.id,
                         reply, reply_to_message_id=message.message_id)


def ticker_info(message):
    result = yf.Ticker(message)
    return result


def get_start_date_dividends(message):
    global start_date
    start_date = message.text
    bot.send_message(message.from_user.id, 'По какой день тебя интересует история выплаты дивидендов?')
    bot.send_message(message.from_user.id,
                     '_Введи дату в формате YYYY-MM-DD_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, get_end_date_dividends)


def get_end_date_dividends(message):
    global end_date
    end_date = message.text
    bot.send_message(message.from_user.id, 'История выплаты дивидендов какой компании тебя интересует?')
    bot.send_message(message.from_user.id,
                     '_Введи тикер компании_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, ticker_dividends)


def get_start_date_recommendations(message):
    global start_date
    start_date = message.text
    bot.send_message(message.from_user.id, 'По какой день тебя интересуют прогнозы аналитиков?')
    bot.send_message(message.from_user.id,
                     '_Введи дату в формате YYYY-MM-DD_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, get_end_date_recommendations)


def get_end_date_recommendations(message):
    global end_date
    end_date = message.text
    bot.send_message(message.from_user.id, 'Прогнозы аналитиков о какой компании тебя интересует?')
    bot.send_message(message.from_user.id,
                     '_Введи тикер компании_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, ticker_recommendations)


def get_start_date_history(message):
    global start_date
    start_date = message.text
    bot.send_message(message.from_user.id, 'По какой день тебя интересует сводка?')
    bot.send_message(message.from_user.id,
                     '_Введи дату в формате YYYY-MM-DD_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, get_end_date_history)


def get_end_date_history(message):
    global end_date
    end_date = message.text
    bot.send_message(message.from_user.id, 'Данные по торгам какой компании тебя интересуют?')
    bot.send_message(message.from_user.id,
                     '_Введи тикер компании_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, ticker_history)


def get_start_date_plot(message):
    global start_date
    start_date = message.text
    bot.send_message(message.from_user.id, 'По какой день тебя интересуют котировки акций?')
    bot.send_message(message.from_user.id,
                     '_Введи дату в формате YYYY-MM-DD_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, get_end_date_plot)


def get_end_date_plot(message):
    global end_date
    end_date = message.text
    bot.send_message(message.from_user.id, 'С каким интервалом котировки акций компании тебя интересуют?')
    bot.send_message(message.from_user.id,
                     '_Пример интервалов: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo_',
                     parse_mode='Markdown')
    bot.register_next_step_handler(message, get_interval_plot)


def get_interval_plot(message):
    global interval
    interval = message.text
    bot.send_message(message.from_user.id, 'Котировки акций какой компании тебя интересуют?')
    bot.send_message(message.from_user.id,
                     '_Введи тикер компании_',
                     parse_mode="Markdown")
    bot.register_next_step_handler(message, ticker_plot)


def ticker_information_general(message):
    try:
        information_collector = ''
        ticker = ticker_info(message.text)
        information = ticker.info
        information_dict = {'longName': 'Название компании', 'website': 'Сайт', 'country': 'Страна',
                            'fullTimeEmployees': 'Число сотрудников', 'sector': 'Сектор',
                            'industry': 'Отрасль'}
        for value in information_dict.keys():
            information_collector += f'*{str(information_dict.get(value))}: *' + str(information[f'{value}']) + '\n'
        bot.send_message(message.from_user.id,
                         information_collector, parse_mode='Markdown', reply_to_message_id=message.message_id,
                         disable_web_page_preview=True)
    except KeyError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


def ticker_information_financial(message):
    try:
        information_collector = ''
        ticker = ticker_info(message.text)
        information = ticker.info
        information_dict = {'currency': 'Валюта торгов',
                            'marketCap': 'Рыночная капитализация',
                            'ebitda': 'Ebitda',
                            'forwardPE': 'Форвардный P/E',
                            'priceToSalesTrailing12Months': 'P/S',
                            'trailingEps': 'EPS',
                            'forwardEps': 'Форвардный EPS',
                            'returnOnAssets': 'ROA',
                            'returnOnEquity': 'ROE',
                            'debtToEquity': 'D/E',
                            'fiftyTwoWeekLow': '52 w Low',
                            'fiftyTwoWeekHigh': '52 w High',
                            'dayLow': 'Day Low',
                            'dayHigh': 'Day High',
                            'fiftyDayAverage': '50 day SMA',
                            'averageVolume': 'Средний объем торгов',
                            'beta': 'Beta',
                            'payoutRatio': 'DPR',
                            'dividendRate': 'Див доходность'
                            }
        for value in information_dict.keys():
            information_collector += f'*{str(information_dict.get(value))}: *' + str(information[f'{value}'])
            if value in ['marketCap', 'ebitda', 'trailingEps', 'forwardEps', 'fiftyTwoWeekLow',
                         'fiftyTwoWeekHigh', 'dayLow', 'dayHigh', 'fiftyDayAverage', 'averageVolume']:
                information_collector += ' ' + str(information['currency'])
            elif value == 'dividendRate' or value == 'debtToEquity':
                information_collector += '%'
            information_collector += '\n'
        bot.send_message(message.from_user.id,
                         information_collector, parse_mode="Markdown", reply_to_message_id=message.message_id,
                         disable_web_page_preview=True)
    except KeyError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


def ticker_history(message):
    try:
        ticker = ticker_info(message.text)
        df_history = ticker.history(start=start_date, end=end_date, interval='1d')
        df_history.reset_index(inplace=True)
        df_history.drop(['Dividends', 'Stock Splits'], axis=1, inplace=True)
        df_history = df_history.round(2)
        dfi.export(df_history, 'C:/Users/tkhayrutdinov/dataframe_history.png')
        photo = open(r'C:/Users/tkhayrutdinov/dataframe_history.png', 'rb')
        reply = f'Статистика по торгам для тикера *{message.text.upper()}* в период с *{start_date}* по *{end_date}*'
        bot.send_message(message.from_user.id,
                         reply, parse_mode='Markdown', reply_to_message_id=message.message_id)
        bot.send_photo(message.from_user.id,
                       photo=photo)
    except ValueError:
        reply = 'Ты ввёл слишком большой диапазон или неправильно указал дату.'
        bot.send_message(message.chat.id,
                         reply)
    except KeyError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


def ticker_recommendations(message):
    try:
        ticker = ticker_info(message.text)
        df_recommendations = ticker.recommendations
        df_recommendations.reset_index(inplace=True)
        df_recommendations = df_recommendations[df_recommendations['Date'] >= start_date]
        df_recommendations = df_recommendations[df_recommendations['Date'] <= end_date]
        df_recommendations.reset_index(inplace=True)
        df_recommendations.rename(columns={'Date': 'Datetime'}, inplace=True)
        df_recommendations['Date'] = df_recommendations['Datetime'].dt.date
        df_recommendations['Date'] = df_recommendations['Date'].astype('datetime64[ns]')
        ticker_df_to_merge = ticker.history(start=start_date, end=end_date, interval='1d')
        ticker_df_to_merge.reset_index(inplace=True)
        df_recommendations = ticker_df_to_merge.merge(df_recommendations, on='Date', how='right')
        df_recommendations.drop(['index', 'Datetime', 'Open', 'Close', 'Volume', 'Dividends', 'Stock Splits'], axis=1,
                                inplace=True)
        df_recommendations = df_recommendations.round(2)
        dfi.export(df_recommendations, 'C:/Users/tkhayrutdinov/dataframe_recommendations.png')
        photo = open(r'C:/Users/tkhayrutdinov/dataframe_recommendations.png', 'rb')
        reply = f'Прогнозы аналитиков по тикеру *{message.text.upper()}* в период с *{start_date}* по *{end_date}*'
        bot.send_message(message.from_user.id,
                         reply, parse_mode='Markdown', reply_to_message_id=message.message_id)
        bot.send_photo(message.from_user.id,
                       photo=photo)
    except TypeError:
        reply = 'Ты неправильно указал дату.'
        bot.send_message(message.chat.id,
                         reply)
    except AttributeError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


def ticker_news(message):
    ticker_news_collector = '*Вот сводка последних новостей по данной компании:*' + '\n' + '\n'
    ticker = ticker_info(message.text)
    ticker_news_agg = ticker.news
    for news in ticker_news_agg:
        title = '*Заголовок: *' + news['title'] + '\n'
        link = '*Ссылка: *' + news['link'] + '\n'
        ticker_news_collector += title + link + '\n'
    bot.send_message(message.from_user.id,
                     ticker_news_collector, parse_mode='Markdown', disable_web_page_preview=True,
                     reply_to_message_id=message.message_id)


def ticker_isin(message):
    ticker_isin_agg = ticker_info(message.text)
    ticker_isin_agg = ticker_isin_agg.isin
    ticker_isin_collector = f'ISIN номер данной бумаги: *{ticker_isin_agg}*'
    bot.send_message(message.from_user.id,
                     ticker_isin_collector, parse_mode='Markdown', reply_to_message_id=message.message_id)


def ticker_dividends(message):
    try:
        ticker = ticker_info(message.text)
        result_temp = ticker.dividends
        df_dividends = pd.DataFrame(result_temp)
        df_dividends.reset_index(inplace=True)
        df_dividends = df_dividends[df_dividends['Date'] >= start_date]
        df_dividends = df_dividends[df_dividends['Date'] <= end_date]
        df_dividends.reset_index(inplace=True)
        df_dividends.drop('index', axis=1, inplace=True)
        dfi.export(df_dividends, 'C:/Users/tkhayrutdinov/dataframe_dividends.png')
        photo = open(r'C:/Users/tkhayrutdinov/dataframe_dividends.png', 'rb')
        bot.send_photo(message.from_user.id,
                       photo=photo, reply_to_message_id=message.message_id)
    except TypeError:
        reply = 'Ты неправильно указал дату.'
        bot.send_message(message.chat.id,
                         reply)
    except KeyError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


def ticker_plot(message):
    try:
        ticker = ticker_info(message.text)
        information = ticker.info
        df_plot = ticker.history(start=start_date, end=end_date, interval=interval)
        df_plot.reset_index(inplace=True)
        df_plot.columns.values[0] = 'Datetime'
        plt.plot(df_plot['Datetime'], df_plot['Open'])
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.xlabel(f"Дата торгов тикера {message.text.upper()}")
        plt.ylabel(f"Стоимость бумаги, {information['currency']}")
        plt.savefig('C:/Users/tkhayrutdinov/plot.png', bbox_inches='tight')
        plt.clf()
        photo = open(r'C:/Users/tkhayrutdinov/plot.png', 'rb')
        bot.send_photo(message.from_user.id,
                       photo=photo, reply_to_message_id=message.message_id)
    except ValueError:
        reply = 'Ты неправильно указал дату.'
        bot.send_message(message.chat.id,
                         reply)
    except KeyError:
        reply = 'Скорее всего, такого тикера не существует.'
        bot.send_message(message.chat.id,
                         reply)


bot.polling(none_stop=True, interval=0)
