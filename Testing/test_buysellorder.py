from locust import HttpUser, TaskSet, task, between
import json
from bs4 import BeautifulSoup
import string
import random
import logging, sys
import psycopg2, config

def print_msgs(rep):
    soup = BeautifulSoup(rep.text,'html.parser')
    txts=soup.find_all('div',{'class':'alert'})
    if len(txts)!=0:
        print([x.text.strip() for x in txts])

### Brokers for load testing all registered at eid 1, 2, 3
brokers = [[17, 'ThomasKMorgan'], [18, 'JimMMendez'], [20, 'AnthonyYWinkelman'], [28, 'MelvinAMunoz']]
### Stock i listed at exchange i + 1
stocks = [[['86', 'APAM']   , ['582', 'MT']],
          [['157', 'CABK']  , ['277', 'ELE']],
          [['10', 'AAL']    , ['11', 'AAP']]
          ]

client_portfolio = [
                    [[[77, 'RobertHFlanders'], [83, 'EmmaJLawless']], 
                     [[56, 'KarenEChen'], [174, 'HannahRHickman']]],
                    [[[124, 'NathanWLoudermilk'], [313, 'DelbertASlater']], 
                     [[92, 'EmmaJLawless'], [274, 'ChristinaRHayse']]],
                    [[[115, 'JohnJPrange'], [218, 'ShirleyRLappin']], 
                     [[917, 'BrendaJFiore'], [933, 'ChristopherLZimmerman']]]
                    ] 

class BrokerUniqueTests(HttpUser):
    cntr = 0
    weight = 4
    wait_time = between(10, 12)
    def on_start(self):
        self.authenticated = False
        if BrokerUniqueTests.cntr < len(brokers):
            self.var_bid     = brokers[BrokerUniqueTests.cntr][0]
            self.var_name    = brokers[BrokerUniqueTests.cntr][1]
            BrokerUniqueTests.cntr += 1
            self.conn = psycopg2.connect(dbname = config.name, user = config.user, password = config.pswd, host = config.host, port = config.port)
            self.login()

    def login(self):
        response = self.client.get('login')
        # print(response.cookies)
        csrftoken = response.cookies['csrftoken']
        rep = self.client.post('login',
                         {'username': self.var_name, 'password': self.var_name, 'broker_login':'Login'},
                         headers={'X-CSRFToken': csrftoken}, allow_redirects=True)
        # print(dir(rep))
        # print_msgs(rep)
        logging.info('Login with %s ID and %s NAME', self.var_bid, self.var_name)
        self.authenticated = True

    @task
    def approve_order(self):
        if not self.authenticated:
            logging.info('Invalid Broker Entered')
            return

        curr    = self.conn.cursor()
        curr.execute(f'SELECT order_id from market_pendingorder where bid = {self.var_bid}')
        result_set = curr.fetchall()

        for order_id in result_set:
            response = self.client.get(f'broker/approve_order?order={order_id[0]}')

class ClientUniqueTests(HttpUser):
    cntr = 0
    weight = 12
    wait_time = between(2, 3)
    def on_start(self):
        self.authenticated = False
        if ClientUniqueTests.cntr < 12:
            self.eid  = ClientUniqueTests.cntr//4
            self.sid  = (ClientUniqueTests.cntr%4)//2
            self.clid = (ClientUniqueTests.cntr)%2

            self.var_folio_id   = client_portfolio[self.eid][self.sid][self.clid][0]
            self.var_name       = client_portfolio[self.eid][self.sid][self.clid][1]
            self.var_eid        = self.eid + 1
            self.var_sid        = stocks[self.eid][self.sid][0]
            ClientUniqueTests.cntr += 1
            self.login()

    def login(self):
        response = self.client.get('login')
        csrftoken = response.cookies['csrftoken']
        rep=self.client.post('login',
                         {'username': self.var_name, 'password': self.var_name, 'client_login':'Login'},
                         headers={'X-CSRFToken': csrftoken}, allow_redirects=True)
        logging.info('Login with %s FOLIO_ID and %s NAME', self.var_folio_id, self.var_name)
        self.authenticated = True

    @task
    def place_order(self):
        if not self.authenticated:
            logging.info('Invalid Client Entered')
            return

        response = self.client.get('client/place_order')
        csrftoken = response.cookies['csrftoken']

        order_type = 'Buy' if self.clid == 0 else 'Sell'
        quantity   = 2 + random.randrange(0, 3)
        price      = 10 + random.randrange(0, 6)
        var_bid    = brokers[random.randrange(0,4)][0]
        rep = self.client.post('client/place_order',
                                {'order_type': order_type, 'quantity': quantity, 'portfolio': self.var_folio_id,
                                 'stock': self.var_sid, 'exchange': self.var_eid, 'broker': var_bid,
                                 'price': price, 'submit': 'Place Order'},
                         headers={'X-CSRFToken': csrftoken}, allow_redirects=True)