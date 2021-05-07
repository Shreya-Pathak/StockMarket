from django.db import models
from django.db import DEFAULT_DB_ALIAS
from django.db.transaction import Atomic, get_connection
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager
from datetime import timedelta


class Stock(models.Model):
    sid = models.AutoField(primary_key=True, db_column='sid')
    ticker = models.TextField(unique=True)
    total_stocks = models.BigIntegerField(blank=False, null=False)

    def __str__(self):
        return self.ticker


class Exchange(models.Model):
    eid = models.AutoField(primary_key=True, db_column='eid')
    name = models.TextField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.name


class Indices(models.Model):
    iid = models.AutoField(primary_key=True, db_column='iid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    index_name = models.TextField(unique=True, blank=False, null=False)
    ticker = models.TextField(unique=True, blank=False, null=False)
    last_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    change = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_divisor = models.DecimalField(max_digits=30, decimal_places=4, default=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['eid', 'index_name'], name='unique_index_exchange')]


class Company(models.Model):
    cid = models.OneToOneField(Stock, models.DO_NOTHING, primary_key=True, db_column='cid')
    name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    logo = models.TextField(blank=False, null=False, default='https://logo.clearbit.com/clearbit.com')
    zipcode = models.TextField(blank=True, null=True)
    sector = models.TextField(blank=True, null=True, default='Miscellaneous')
    summary = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    website = models.TextField(blank=True, null=True)
    employees = models.IntegerField(blank=True, null=True)
    industry = models.TextField(blank=True, null=True)


class Person(models.Model):
    pid = models.AutoField(primary_key=True, db_column='pid')
    name = models.TextField(blank=False, null=False)
    address = models.TextField(blank=True, null=True)
    telephone = models.TextField(blank=True, null=True)



class Client(models.Model):
    clid = models.OneToOneField(Person, models.DO_NOTHING, primary_key=True, db_column='clid')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    username = models.TextField(unique=True, blank=False, null=False)


class Broker(models.Model):
    bid = models.OneToOneField(Person, models.DO_NOTHING, primary_key=True, db_column='bid')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    username = models.TextField(unique=True, blank=False, null=False)
    commission = models.DecimalField(max_digits=15, decimal_places=2)
    latency = models.IntegerField(blank=False, null=False, default=0)
    orders_approved = models.IntegerField(blank=False, null=False, default=0)

    def __str__(self):
        latency = str(timedelta(seconds=self.latency))
        return f'{self.bid.name} - {self.commission}% - {latency}'


class Portfolio(models.Model):
    folio_id = models.AutoField(primary_key=True, db_column='folio_id')
    clid = models.ForeignKey(Client, models.DO_NOTHING, db_column='clid')
    pname = models.TextField(blank=False, null=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['clid', 'pname'], name='client_portfolio_pkey')]

    def __str__(self):
        return self.pname


class Wishlist(models.Model):
    wish_id = models.AutoField(primary_key=True, db_column='wish_id')
    clid = models.ForeignKey(Client, models.DO_NOTHING, db_column='clid')
    wname = models.TextField(blank=False, null=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['clid', 'wname'], name='client_wishlist_pkey')]


class BankAccount(models.Model):
    account_number = models.BigIntegerField(primary_key=True, db_column='account_number')
    bank_name = models.TextField(blank=False, null=False)
    pid = models.ForeignKey(Person, models.DO_NOTHING, default=0, db_column='pid')
    balance = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(balance__gte=0), name='valid_balance')]


class ListedAt(models.Model):
    listed_id = models.AutoField(primary_key=True, db_column='listed_id')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    last_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    change = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['sid', 'eid'], name='exchange_stock_pkey')]


class StockPriceHistory(models.Model):
    stock_price_id = models.AutoField(primary_key=True, db_column='stock_price_id')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    creation_time = TimescaleDateTimeField(interval="1 day")
    price = models.DecimalField(max_digits=15, decimal_places=2)
    objects = models.Manager()
    timescale = TimescaleManager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['sid', 'eid', 'creation_time', 'price'], name='stock_price_pkey')]
        get_latest_by = 'creation_time'


class IndexPriceHistory(models.Model):
    index_price_id = models.AutoField(primary_key=True, db_column='index_price_id')
    iid = models.ForeignKey(Indices, models.DO_NOTHING, db_column='iid')
    creation_time = TimescaleDateTimeField(interval="1 day")
    price = models.DecimalField(max_digits=15, decimal_places=2)
    objects = models.Manager()
    timescale = TimescaleManager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['iid', 'creation_time', 'price'], name='index_price_pkey')]
        get_latest_by = 'creation_time'


class PartOfIndex(models.Model):
    partof_id = models.AutoField(primary_key=True, db_column='partof_id')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    iid = models.ForeignKey(Indices, models.DO_NOTHING, db_column='iid')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['sid', 'iid'], name='stock_index_pkey')]


class StockWishlist(models.Model):
    stock_wish_id = models.AutoField(primary_key=True, db_column='stock_wish_id')
    wish_id = models.ForeignKey(Wishlist, models.DO_NOTHING, db_column='wish_id')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['wish_id', 'sid'], name='wish_stock_pkey')]


class Recommendation(models.Model):
    rec_id = models.AutoField(primary_key=True, db_column='rec_id')
    bid = models.ForeignKey(Broker, models.DO_NOTHING, db_column='bid')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['bid', 'sid'], name='broker_stock_recommend_pkey')]


class RegisteredAt(models.Model):
    reg_id = models.AutoField(primary_key=True, db_column='reg_id')
    bid = models.ForeignKey(Broker, models.DO_NOTHING, db_column='bid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['bid', 'eid'], name='broker_exchange_reg_pkey')]


class Holdings(models.Model):
    hold_id = models.AutoField(primary_key=True, db_column='hold_id')
    folio_id = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='folio_id')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    quantity = models.BigIntegerField(blank=False, null=False, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['folio_id', 'sid'], name='portfolio_stock_pkey')]


class OldOrder(models.Model):
    order_id = models.AutoField(primary_key=True, db_column='order_id')
    folio_id = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='folio_id')
    bid = models.ForeignKey(Broker, models.DO_NOTHING, db_column='bid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    quantity = models.IntegerField(blank=False, null=False)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    creation_time = TimescaleDateTimeField(interval="1 day")
    order_type = models.TextField(blank=False, choices=[('Buy', 'Buy'), ('Sell', 'Sell')])
    objects = models.Manager()
    timescale = TimescaleManager()


class PendingOrder(models.Model):
    order_id = models.AutoField(primary_key=True, db_column='order_id')
    folio_id = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='folio_id')
    bid = models.ForeignKey(Broker, models.DO_NOTHING, db_column='bid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    quantity = models.IntegerField(blank=False, null=False)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    creation_time = TimescaleDateTimeField(interval="1 day")
    order_type = models.TextField(blank=False, choices=[('Buy', 'Buy'), ('Sell', 'Sell')])
    objects = models.Manager()
    timescale = TimescaleManager()


class BuySellOrder(models.Model):
    order_id = models.AutoField(primary_key=True, db_column='order_id')
    folio_id = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='folio_id')
    bid = models.ForeignKey(Broker, models.DO_NOTHING, db_column='bid')
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    sid = models.ForeignKey(Stock, models.DO_NOTHING, db_column='sid')
    quantity = models.IntegerField(blank=False, null=False)
    completed_quantity = models.IntegerField(blank=False, null=False)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    creation_time = TimescaleDateTimeField(interval="1 day")
    order_type = models.TextField(blank=False, choices=[('Buy', 'Buy'), ('Sell', 'Sell')])
    objects = models.Manager()
    timescale = TimescaleManager()

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(completed_quantity__lte=models.F('quantity')), name='valid_buysell_state_check')]
        indexes = [
           models.Index(fields=['bid','sid'])
           ]


class LockedAtomicTransaction(Atomic):
    """
    Does a atomic transaction, but also locks the entire table for any transactions, for the duration of this
    transaction. Although this is the only way to avoid concurrency issues in certain situations, it should be used with
    caution, since it has impacts on performance, for obvious reasons...
    Usage:
        # ModelsToLock = [ModelA, ModelB, ....]
        with LockedAtomicTransaction(ModelsToLock):
            # do whatever you want to do
            ModelA.objects.create()
    """
    def __init__(self, models, using=None, savepoint=None):
        if using is None:
            using = DEFAULT_DB_ALIAS
        super().__init__(using, savepoint)
        self.models = models

    def __enter__(self):
        super(LockedAtomicTransaction, self).__enter__()
        cursor = None
        try:
            cursor = get_connection(self.using).cursor()
            model_names = [model._meta.db_table for model in self.models]
            cursor.execute(f"LOCK TABLE {', '.join(model_names)};")
        finally:
            if cursor and not cursor.closed:
                cursor.close()
