import sys, os, django

project_dir = "../"
sys.path.append(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StockMarket.settings')
django.setup()

from django.contrib.auth.models import User
import market.models as models
from tqdm import tqdm
import random
import yfinance as yf
import pandas as pd
from pytickersymbols import PyTickerSymbols

random.seed(69)


def get_index_data():
    stock_data = PyTickerSymbols()
    indices = stock_data.get_all_indices()

    bad = '-'
    exchanges = set()
    companies = {}
    index_exchange = {}
    composition = {}
    stock_listed_at = {}

    prefs = ['BME', 'LON', 'OTCMKTS']

    for index in indices:
        cur = list(stock_data.get_stocks_by_index(index))
        is_first = True
        current_exchanges = set()
        for stock in cur:
            ex_variations = [(s['yahoo'], s['google'].split(':')[0]) for s in stock['symbols'] if s['google'].split(':')[0] != bad]

            sym = stock['symbol']
            if not sym or not ex_variations:
                continue
            sym = sym.split(':')[-1]

            if index not in composition.keys():
                composition[index] = []
            composition[index].append(sym)

            if sym not in companies.keys():
                companies[sym] = {'yahoo,exchange': set()}
                assert stock['name']
                assert stock['country']
                companies[sym]['name'] = stock['name']
                companies[sym]['country'] = stock['country']

            if sym not in stock_listed_at.keys():
                stock_listed_at[sym] = set()

            for e in ex_variations:
                companies[sym]['yahoo,exchange'].add(e)
                stock_listed_at[sym].add(e[1])

            if is_first:
                [current_exchanges.add(t[1]) for t in ex_variations]
                is_first = False
            else:
                good = set()
                for ex in ex_variations:
                    if ex[1] in current_exchanges:
                        good.add(ex[1])
                current_exchanges = good

            [exchanges.add(t[1]) for t in ex_variations]
        current_exchanges = list(current_exchanges)
        if len(current_exchanges) == 1:
            index_exchange[index] = current_exchanges[0]
        elif len(current_exchanges) > 1:
            for p in prefs:
                if p in current_exchanges:
                    index_exchange[index] = p
                    break
        if index not in index_exchange.keys():
            composition.pop(index, None)

    exchanges = sorted(list(exchanges))
    return exchanges, composition, index_exchange, stock_listed_at


def insert_stocks_companies():
    df = pd.read_csv('csv/companies.csv', sep=',')
    df.fillna('', inplace=True)
    stocks, companies = [], []

    already = set()
    for st in models.Stock.objects.all():
        already.add(st.ticker)

    for i, row in df.iterrows():
        if row['ticker'] in already:
            continue
        st = models.Stock(ticker=row['ticker'], total_stocks=row['total_stocks'])
        stocks.append(st)
    if len(stocks) > 0:
        models.Stock.objects.bulk_create(stocks)

    for i, row in df.iterrows():
        if row['ticker'] in already:
            continue
        if not row['logo'].strip():
            row['logo'] = 'https://logo.clearbit.com/clearbit.com'
        if not row['sector'].strip():
            row['sector'] = 'Miscellaneous'
        comp = models.Company(cid=stocks[i], name=row['name'], address=row['address'], country=row['country'], logo=row['logo'], zipcode=row['zipcode'], sector=row['sector'], summary=row['summary'], city=row['city'], phone=str(row['phone']), website=row['website'], employees=row['employees'], industry=row['industry'])
        companies.append(comp)
    if len(companies) > 0:
        models.Company.objects.bulk_create(companies)


index_tickers = {'EURO STOXX 50': 'FEZ', 'SDAX': '^SDAXI', 'CAC Mid 60': '^CM100', 'DAX': '^GDAXI', 'S&P 100': '^OEX', 'OMX Stockholm 30': '^OMX', 'S&P 500': '^GSPC', 'NASDAQ 100': '^NDX', 'AEX': '^AEX', 'DOW JONES': '^DJI', 'IBEX 35': '^IBEX', 'MOEX': 'IMOEX.ME', 'BEL 20': '^BFX', 'MDAX': '^MDAXI', 'CAC 40': '^FCHI', 'TECDAX': '^TECDAX', 'FTSE 100': '^FTSE', 'OMX Helsinki 25': '^OMXH25'}


def insert_exchanges_indices_partof_listedat():
    exchanges, composition, index_exchange, stock_listed_at = get_index_data()

    exchange_map = {}
    exchange_objs = []
    for ex_name in exchanges:
        ex = models.Exchange(name=ex_name)
        exchange_objs.append(ex)
        exchange_map[ex_name] = ex
    models.Exchange.objects.bulk_create(exchange_objs)

    indices = []
    indices_map = {}
    for index, ex in sorted(index_exchange.items()):
        idx = models.Indices(eid=exchange_map[ex], index_name=index, ticker=index_tickers[index])
        indices.append(idx)
        indices_map[index] = idx
    models.Indices.objects.bulk_create(indices)

    ticker_id = {}
    listedats = []
    for st in models.Stock.objects.all():
        ticker_id[st.ticker] = st
        listed_at_exchange = None
        if st.ticker not in stock_listed_at.keys():
            for index, tickers in composition.items():
                if st.ticker in tickers:
                    listed_at_exchange = [index_exchange[index]]
                    break
            if listed_at_exchange is None:
                listed_at_exchange = [random.choice(exchanges)]
        else:
            listed_at_exchange = stock_listed_at[st.ticker]
        for ex_name in listed_at_exchange:
            listed = models.ListedAt(sid=st, eid=exchange_map[ex_name])
            listedats.append(listed)
    models.ListedAt.objects.bulk_create(listedats)

    partofs = []
    for index, tickers in sorted(composition.items()):
        idx = indices_map[index]
        for ticker in set(tickers):
            if ticker not in ticker_id.keys():
                continue
            stock = ticker_id[ticker]
            part = models.PartOfIndex(sid=stock, iid=idx)
            partofs.append(part)
    models.PartOfIndex.objects.bulk_create(partofs)


insert_stocks_companies()
insert_exchanges_indices_partof_listedat()
