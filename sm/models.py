# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class BankAccount(models.Model):
    account_number = models.IntegerField(primary_key=True)
    clid = models.ForeignKey('Client', models.DO_NOTHING, db_column='clid', blank=True, null=True)
    balance = models.DecimalField(max_digits=65535, decimal_places=65535)

    class Meta:
        managed = False
        db_table = 'bank_account'


class Broker(models.Model):
    bid = models.OneToOneField('Person', models.DO_NOTHING, db_column='bid', primary_key=True)
    commission = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    latency = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'broker'


class Buyorder(models.Model):
    orderid = models.IntegerField(primary_key=True)
    clid = models.ForeignKey('Portfolio', models.DO_NOTHING, db_column='clid', blank=True, null=True)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey('Registeredat', models.DO_NOTHING, db_column='bid', blank=True, null=True)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)
    initial_quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    completed_quantity = models.IntegerField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'buyorder'


class Client(models.Model):
    clid = models.OneToOneField('Person', models.DO_NOTHING, db_column='clid', primary_key=True)
    email = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'client'


class Company(models.Model):
    cid = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'company'


class Exchange(models.Model):
    eid = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exchange'


class Indices(models.Model):
    eid = models.OneToOneField(Exchange, models.DO_NOTHING, db_column='eid', primary_key=True)
    iid = models.IntegerField()
    index_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'indices'
        unique_together = (('eid', 'iid'),)


class Listedat(models.Model):
    ticker = models.OneToOneField('Stock', models.DO_NOTHING, db_column='ticker', primary_key=True)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')

    class Meta:
        managed = False
        db_table = 'listedat'
        unique_together = (('ticker', 'eid'),)


class Oldorder(models.Model):
    orderid = models.IntegerField(primary_key=True)
    clid = models.ForeignKey('Portfolio', models.DO_NOTHING, db_column='clid', blank=True, null=True)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey('Registeredat', models.DO_NOTHING, db_column='bid', blank=True, null=True)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    order_type = models.TextField()
    creation_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'oldorder'


class Partof(models.Model):
    ticker = models.OneToOneField('Stock', models.DO_NOTHING, db_column='ticker', primary_key=True)
    eid = models.ForeignKey(Indices, models.DO_NOTHING, db_column='eid')
    iid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partof'
        unique_together = (('ticker', 'eid', 'iid'),)


class Person(models.Model):
    pid = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    telephone = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'person'


class Portfolio(models.Model):
    clid = models.OneToOneField(Client, models.DO_NOTHING, db_column='clid', primary_key=True)
    pname = models.TextField()

    class Meta:
        managed = False
        db_table = 'portfolio'
        unique_together = (('clid', 'pname'),)


class Pricehistory(models.Model):
    ticker = models.OneToOneField('Stock', models.DO_NOTHING, db_column='ticker', primary_key=True)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')
    creation_time = models.DateTimeField()
    price = models.DecimalField(max_digits=65535, decimal_places=65535)

    class Meta:
        managed = False
        db_table = 'pricehistory'
        unique_together = (('ticker', 'eid', 'creation_time', 'price'),)


class Recommendation(models.Model):
    bid = models.OneToOneField(Broker, models.DO_NOTHING, db_column='bid', primary_key=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker')

    class Meta:
        managed = False
        db_table = 'recommendation'
        unique_together = (('bid', 'ticker'),)


class Registeredat(models.Model):
    bid = models.OneToOneField(Broker, models.DO_NOTHING, db_column='bid', primary_key=True)
    eid = models.ForeignKey(Exchange, models.DO_NOTHING, db_column='eid')

    class Meta:
        managed = False
        db_table = 'registeredat'
        unique_together = (('bid', 'eid'),)


class Sellorder(models.Model):
    orderid = models.IntegerField(primary_key=True)
    clid = models.ForeignKey(Portfolio, models.DO_NOTHING, db_column='clid', blank=True, null=True)
    pname = models.TextField(blank=True, null=True)
    bid = models.ForeignKey(Registeredat, models.DO_NOTHING, db_column='bid', blank=True, null=True)
    eid = models.IntegerField(blank=True, null=True)
    ticker = models.ForeignKey('Stock', models.DO_NOTHING, db_column='ticker', blank=True, null=True)
    initial_quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    completed_quantity = models.IntegerField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sellorder'


class Stock(models.Model):
    ticker = models.TextField(primary_key=True)
    total_stocks = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock'


class Stockwishlist(models.Model):
    clid = models.OneToOneField('Wishlist', models.DO_NOTHING, db_column='clid', primary_key=True)
    wname = models.TextField()
    ticker = models.ForeignKey(Stock, models.DO_NOTHING, db_column='ticker')

    class Meta:
        managed = False
        db_table = 'stockwishlist'
        unique_together = (('clid', 'wname', 'ticker'),)


class Wishlist(models.Model):
    clid = models.OneToOneField(Client, models.DO_NOTHING, db_column='clid', primary_key=True)
    wname = models.TextField()

    class Meta:
        managed = False
        db_table = 'wishlist'
        unique_together = (('clid', 'wname'),)
