import sys, os, django, csv

project_dir = "../"
sys.path.append(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StockMarket.settings')
django.setup()

from django.contrib.auth.models import User
import market.models as models
import pandas as pd
from tqdm import tqdm
from decimal import Decimal
import random
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.contrib.auth.hashers import make_password
from django_bulk_update.helper import bulk_update

random.seed(69)


def insert_user_person_client_broker():
    print('Creating users')
    df = pd.read_csv('csv/persons.csv', sep=',', nrows=100)
    users, persons = [], []
    for i, row in tqdm(df.iterrows(), total=len(df.index)):
        email = row['EmailAddress']
        username = email.split('@')[0]
        password = make_password(username)
        name = row['GivenName'] + ' ' + row['MiddleInitial'] + '. ' + row['Surname']
        address = row['StreetAddress'] + ', ' + row['City']
        telephone = row['TelephoneNumber'].replace('-', '')
        user = User(username=username, email=email, password=password, first_name=name)
        person = models.Person(name=name, address=address, telephone=telephone)
        users.append(user)
        persons.append(person)

    User.objects.bulk_create(users)
    models.Person.objects.bulk_create(persons)

    clients, brokers = [], []
    for user, person in zip(users, persons):
        # 20% of people are brokers
        balance = random.randint(1e5, 2e5)
        if random.randint(0, 10) < 2:
            # is broker, add registeredat
            commission = random.randint(3, 15) + (random.randint(0, 100) / 100)
            broker = models.Broker(bid=person, username=user.username, balance=balance, commission=commission)
            brokers.append(broker)
        else:
            # is client, add portfolio, holdings
            client = models.Client(clid=person, username=user.username, balance=balance)
            clients.append(client)

    models.Client.objects.bulk_create(clients)
    models.Broker.objects.bulk_create(brokers)


def insert_reg_at():
    print('Inserting RegisteredAt tuples')
    regats = []
    exchanges = list(models.Exchange.objects.all())
    for broker in models.Broker.objects.all():
        num = random.randint(1, len(exchanges))
        for ex in random.sample(exchanges, num):
            cur = models.RegisteredAt(bid=broker, eid=ex)
            regats.append(cur)
    models.RegisteredAt.objects.bulk_create(regats)


def insert_stockprice(batch_size=100000):
    print('Inserting Stock Prices')
    ticker_obj = {}
    for st in models.Stock.objects.all():
        ticker_obj[st.ticker] = st
    exchange_obj = {}
    for ex in models.Exchange.objects.all():
        exchange_obj[ex.name] = ex

    prices = []
    with open('csv/prices_30day.csv', 'r') as fp:
        reader = csv.reader(fp)
        header = None
        for row in reader:
            if header is None:
                header = {}
                for i, h in enumerate(row):
                    header[h] = i
            else:
                stock = row[header['ticker']]
                exchange = row[header['exchange']]
                stamp = row[header['creation_time']]
                price = float(row[header['price']])
                if price != price:
                    continue
                if stock not in ticker_obj.keys():
                    continue
                if exchange not in exchange_obj.keys():
                    continue
                stock = ticker_obj[stock]
                exchange = exchange_obj[exchange]
                stamp = make_aware(datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S'))
                cur = models.StockPriceHistory(sid=stock, eid=exchange, creation_time=stamp, price=price)
                if len(prices) >= batch_size:
                    models.StockPriceHistory.objects.bulk_create(prices, ignore_conflicts=True)
                    print(f'Saved {batch_size} rows')
                    prices = []
                prices.append(cur)
    if len(prices) > 0:
        models.StockPriceHistory.objects.bulk_create(prices, ignore_conflicts=True)


def insert_last_prices():
    print("Updating Latest Prices")
    listedats = list(models.ListedAt.objects.select_related('sid', 'eid').all())
    last_prices, prices = [], []
    for st_ex in tqdm(listedats):
        try:
            obj = models.StockPriceHistory.timescale.filter(sid=st_ex.sid, eid=st_ex.eid).latest()
            price = obj.price
            stamp = obj.creation_time
        except Exception as e:
            stamp = make_aware(datetime.now())
            price = Decimal(random.randint(30, 90) + (random.randint(0, 100) / 100))
            cur = models.StockPriceHistory(sid=st_ex.sid, eid=st_ex.eid, creation_time=stamp, price=price)
            prices.append(cur)
        finally:
            change = random.randint(-10, 10) + (random.randint(0, 100) / 100)
            new_stamp = stamp + timedelta(seconds=random.randint(10, 20))
            new_price = price * Decimal(1 + change / 100)
            st_ex.last_price = new_price
            st_ex.change = change
            cur = models.StockPriceHistory(sid=st_ex.sid, eid=st_ex.eid, creation_time=new_stamp, price=new_price)
            prices.append(cur)
            last_prices.append(st_ex)
    bulk_update(last_prices, update_fields=['last_price', 'change'], batch_size=1000)
    models.StockPriceHistory.objects.bulk_create(prices)

    last_prices, prices = [], []
    indices = list(models.Indices.objects.all())
    for idx in tqdm(indices):
        try:
            obj = models.IndexPriceHistory.timescale.filter(iid=idx.iid).latest()
            price = obj.price
            stamp = obj.creation_time
        except Exception as e:
            stamp = make_aware(datetime.now())
            price = Decimal(random.randint(30, 90) + (random.randint(0, 100) / 100))
            cur = models.IndexPriceHistory(iid=idx, creation_time=stamp, price=price)
            prices.append(cur)
        finally:
            change = random.randint(-10, 10) + (random.randint(0, 100) / 100)
            new_stamp = stamp + timedelta(seconds=random.randint(10, 20))
            new_price = price * Decimal(1 + change / 100)
            idx.last_price = new_price
            idx.change = change
            cur = models.IndexPriceHistory(iid=idx, creation_time=new_stamp, price=new_price)
            prices.append(cur)
            last_prices.append(idx)
    bulk_update(last_prices, update_fields=['last_price', 'change'], batch_size=1000)
    models.IndexPriceHistory.objects.bulk_create(prices)


def insert_indexprice(batch_size=100000):
    print('Inserting Index Prices')
    index_obj = {}
    for idx in models.Indices.objects.all():
        index_obj[idx.ticker] = idx

    prices = []
    with open('csv/index_prices.csv', 'r') as fp:
        reader = csv.reader(fp)
        header = None
        for row in reader:
            if header is None:
                header = {}
                for i, h in enumerate(row):
                    header[h] = i
            else:
                index = row[header['ticker']]
                stamp = row[header['creation_time']]
                price = float(row[header['price']])
                if price != price:
                    continue
                if index not in index_obj.keys():
                    continue
                index = index_obj[index]
                stamp = make_aware(datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S'))
                cur = models.IndexPriceHistory(iid=index, creation_time=stamp, price=price)
                if len(prices) >= batch_size:
                    models.IndexPriceHistory.objects.bulk_create(prices, ignore_conflicts=True)
                    print(f'Saved {batch_size} rows')
                    prices = []
                prices.append(cur)
    if len(prices) > 0:
        models.IndexPriceHistory.objects.bulk_create(prices, ignore_conflicts=True)


def insert_portfolio_holdings():
    print("Inserting Portfolio Holdings")
    stocks = list(models.Stock.objects.all())
    last_price, sector = {}, {}
    for stock in tqdm(stocks):
        last_price[stock.sid] = models.ListedAt.objects.filter(sid=stock.sid).first().last_price
        sector[stock.sid] = models.Company.objects.get(cid=stock.sid).sector

    for client in models.Client.objects.all():
        num = random.randint(10, min(len(stocks), 100))
        cur_stocks = random.sample(stocks, num)

        cur_sectors = {}
        for st in cur_stocks:
            if sector[st.sid] not in cur_sectors.keys():
                cur_sectors[sector[st.sid]] = []
            cur_sectors[sector[st.sid]].append(st)

        folios = []
        for cur_sector in cur_sectors.keys():
            folio = models.Portfolio(clid=client, pname=cur_sector)
            folios.append(folio)
            cur_sectors[cur_sector] = [(st, folio) for st in cur_sectors[cur_sector]]
        models.Portfolio.objects.bulk_create(folios)

        holds = []
        for cur_sector, st_list in cur_sectors.items():
            for st, folio in st_list:
                up = max(1, st.total_stocks // 1000)
                quantity = random.randint(0, up)
                total = quantity * last_price[st.sid]
                hold = models.Holdings(folio_id=folio, sid=st, quantity=quantity, total_price=total)
                holds.append(hold)
        models.Holdings.objects.bulk_create(holds)


def generate_bases():
    print("Inserting Bases")
    indices = list(models.Indices.objects.all())
    for index in indices:
        last_value = index.last_price
        market_cap = 0
        for stidx in models.PartOfIndex.objects.filter(iid=index):
            last_price_stock = models.ListedAt.objects.filter(sid=stidx.sid, eid=index.eid).first()
            market_cap += last_price_stock.last_price * stidx.sid.total_stocks
        index.base_divisor = market_cap / last_value
        index.save(update_fields=['base_divisor'])


insert_user_person_client_broker()
insert_reg_at()
insert_stockprice()
insert_indexprice()
insert_last_prices()
insert_portfolio_holdings()
generate_bases()