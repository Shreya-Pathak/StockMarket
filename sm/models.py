from django.db import models
# from timescale.db.models.models import TimescaleModel
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager

# Create your models here.
# class Metric(TimescaleModel):
#    temperature = models.FloatField()

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=False
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# from django.db import models

class Person(models.Model):
    # pid = models.TextField(primary_key=False)
    name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    telephone = models.TextField(blank=True, null=True)
    

class Client(models.Model):
    id = models.OneToOneField('Person', models.DO_NOTHING, db_column='id', primary_key=True)
    email = models.TextField(blank=True, null=True)


class BankAccount(models.Model):
    account_number = models.IntegerField()
    clid = models.ForeignKey('Client', models.DO_NOTHING, db_column='clid', blank=True, null=True,default='')
    balance = models.DecimalField(max_digits=10, decimal_places=5)

    
class Broker(models.Model):
    id = models.OneToOneField('Person', models.DO_NOTHING, db_column='bid', primary_key=True)
    commission = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    latency = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)

    
class Buyorder(models.Model):
    orderid = models.IntegerField(primary_key=False)
    clid = models.ForeignKey('Portfolio', models.DO_NOTHING, db_column='clid', blank=True, null=True,default=0)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey('Registeredat', models.DO_NOTHING, db_column='bid', blank=True, null=True,default=0)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)
    initial_quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    completed_quantity = models.IntegerField(blank=True, null=True)
    creation_time = TimescaleDateTimeField(interval="1 day",blank=True, null=True)
    objects = models.Manager()
    timescale = TimescaleManager()


class Company(models.Model):
    cid = models.IntegerField(primary_key=False)
    name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True,default=0)

    
class Exchange(models.Model):
    # eid = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

class Stock(models.Model):
    ticker = models.TextField(primary_key=True, unique=True)
    total_stocks = models.IntegerField(blank=True, null=True)

class Indices(models.Model):
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid', primary_key=False)
    iid = models.IntegerField()
    index_name = models.TextField(blank=True, null=True)

    
class Listedat(models.Model):
    ticker = models.ForeignKey("Stock", models.DO_NOTHING, db_column='ticker' , to_field='ticker', primary_key=False)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid',default=0)

    
class Oldorder(models.Model):
    orderid = models.IntegerField(primary_key=False)
    clid = models.ForeignKey('Portfolio', models.DO_NOTHING, db_column='clid', blank=True, null=True)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey('Registeredat', models.DO_NOTHING, db_column='bid', blank=True, null=True)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    order_type = models.TextField()
    creation_time = TimescaleDateTimeField(interval="1 day",blank=True, null=True)
    objects = models.Manager()
    timescale = TimescaleManager()

    
class Partof(models.Model):
    ticker = models.OneToOneField('Stock', models.DO_NOTHING, db_column='ticker', primary_key=False)
    eid = models.ForeignKey(Indices, models.DO_NOTHING, db_column='eid',default=0)
    iid = models.IntegerField()

    
class Portfolio(models.Model):
    clid = models.OneToOneField(Client, models.DO_NOTHING, db_column='clid', primary_key=False)
    pname = models.TextField()


class Pricehistory(models.Model):
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', to_field='ticker', primary_key=False,default=0)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid',default=0)
    creation_time = TimescaleDateTimeField(interval="1 day")
    price = models.DecimalField(max_digits=10, decimal_places=5)
    objects = models.Manager()
    timescale = TimescaleManager()


class Recommendation(models.Model):
    bid = models.OneToOneField(Broker, models.DO_NOTHING, db_column='bid', primary_key=False)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker',default=0)

    
class Registeredat(models.Model):
    bid = models.OneToOneField(Broker, models.DO_NOTHING, db_column='bid', primary_key=False)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid',default=0)


class Sellorder(models.Model):
    orderid = models.IntegerField(primary_key=False)
    clid = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='clid', blank=True, null=True)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey(Registeredat, models.DO_NOTHING, db_column='bid', blank=True, null=True,default=0)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True,default=0)
    initial_quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    completed_quantity = models.IntegerField(blank=True, null=True)
    creation_time = TimescaleDateTimeField(interval="1 day",blank=True, null=True)
    objects = models.Manager()
    timescale = TimescaleManager()

    
    
class Stockwishlist(models.Model):
    clid = models.OneToOneField('Wishlist', models.DO_NOTHING, db_column='clid')
    wname = models.TextField()
    ticker = models.ForeignKey(Stock, models.DO_NOTHING, db_column='ticker',default=0)

    
class Wishlist(models.Model):
    clid = models.OneToOneField(Client, models.DO_NOTHING, db_column='clid')
    wname = models.TextField()

    
