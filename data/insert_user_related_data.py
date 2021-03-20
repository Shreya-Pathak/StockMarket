import sys, os, django, csv

project_dir = "../"
sys.path.append(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'StockMarket.settings')
django.setup()

from django.contrib.auth.models import User
import market.models as models
import pandas as pd
from tqdm import tqdm
import random
from datetime import datetime
from django.utils.timezone import make_aware
from django.contrib.auth.hashers import make_password

random.seed(69)

def insert_user_person_client_broker():
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
    regats = []
    exchanges = list(models.Exchange.objects.all())
    for broker in models.Broker.objects.all():
        num = random.randint(1, len(exchanges))
        for ex in random.sample(exchanges, num):
            cur = models.RegisteredAt(bid=broker, eid=ex)
            regats.append(cur)
    models.RegisteredAt.objects.bulk_create(regats)


def insert_stockprice(batch_size=100000):
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
                if price == float('nan'):
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
    listedats = list(models.ListedAt.objects.select_related('sid', 'eid').all())
    last_prices = []
    print("Updating Latest Prices")
    for st_ex in tqdm(listedats):
        try:
            price = models.StockPriceHistory.timescale.filter(sid=st_ex.sid, eid=st_ex.eid).latest().price
        except Exception as e:
            stamp = make_aware(datetime.now())
            price = random.randint(30, 90) + (random.randint(0, 100) / 100)
            cur = models.StockPriceHistory(sid=st_ex.sid, eid=st_ex.eid, creation_time=stamp, price=price)
            cur.save()
        finally:
            last_price = models.Stocklists(sid=st_ex.sid, eid=st_ex.eid, last_price=price)
            last_prices.append(last_price)
    models.Stocklists.objects.bulk_create(last_prices)

    indices = list(models.Indices.objects.all())
    for idx in tqdm(indices):
        try:
            price = models.IndexPriceHistory.timescale.filter(iid=idx.iid).latest().price
        except Exception as e:
            stamp = make_aware(datetime.now())
            price = random.randint(30, 90) + (random.randint(0, 100) / 100)
            cur = models.IndexPriceHistory(iid=idx, creation_time=stamp, price=price)
            cur.save()
        finally:
            idx.last_price = price
            idx.save(update_fields=['last_price'])


def insert_indexprice(batch_size=100000):
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
                if price == float('nan'):
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
    stocks = list(models.Stock.objects.all())
    print("Inserting Portfolio Holdings")
    last_price, sector = {}, {}
    for stock in tqdm(stocks):
        last_price[stock.sid] = models.Stocklists.objects.filter(sid=stock.sid).first().last_price
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
    indices = list(models.Indices.objects.all())
    print("Inserting Bases")
    for index in indices:
        last_value = index.last_price
        market_cap = 0
        for stidx in models.PartOfIndex.objects.filter(iid = index):
                last_price_stock = models.Stocklists.objects.filter(sid = stidx.sid, eid = index.eid).first()
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