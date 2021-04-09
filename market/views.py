from django.shortcuts import render as django_render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Value
from operator import itemgetter
import market.forms as allforms
from io import BytesIO, StringIO
import base64, urllib
import numpy as np
from django.core.serializers.json import DjangoJSONEncoder
from . import models
import random

import matplotlib
matplotlib.use('Agg')
from matplotlib import style
style.use('ggplot')
import matplotlib.pyplot as plt


# Create your views here.
def render(request, html_file, context={}):
	indices = list(models.Indices.objects.all())
	random.shuffle(indices)
	context.update(indices=indices)
	return django_render(request, html_file, context)


def is_client(request):
    if request.user.is_authenticated:
        client = models.Client.objects.filter(username=request.user.username).first()
        return (client is not None)
    return False


def index_view(request):
    return HttpResponseRedirect('stocklist')


def custom_query(query, format_vars=None):
    "executes sql query and returns each row as a dict"
    if not query.endswith(';'): query += ';'
    with connection.cursor() as cursor:
        cursor.execute(query, format_vars)
        if not cursor.description: return None
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows


def stocklist_view(request, page_num=1):
    user_type = 'client' if is_client(request) else 'broker'
    exchange = request.GET.get('exchange', '')
    ticker = request.GET.get('ticker', '')
    order = request.GET.get('order', 'sid__ticker')
    StockLt = models.ListedAt.objects.filter(sid__ticker__icontains=ticker, eid__name__icontains=exchange)
    StockLt = StockLt.select_related('sid', 'eid').order_by(order).all()
    pg = Paginator(StockLt, 8)
    tot_pgs = pg.num_pages
    page_num = min(max(page_num, 1), tot_pgs)
    StockLt = pg.page(page_num).object_list
    if request.method == 'POST':
        form = allforms.SorterForm(request.POST)
        if form.is_valid() and 'sfilt' in request.POST:
            sf = form.cleaned_data['sortfield']  #string of number
            tick = form.cleaned_data['ticker']
            exc = form.cleaned_data['exchange']
            data = StockLt
            order = 'sid__ticker'
            if sf == 'Exchange':
                order = 'eid__name'
            elif sf == 'Latest Price':
                order = 'last_price'
            return redirect(f'/market/stocklist/1/?exchange=' + exc + '&ticker=' + tick + '&order=' + order)
    else:
        form = allforms.SorterForm()
        form['sortfield'].initial = order if order != 'sid__ticker' else 'Ticker'
        data = StockLt
        context = {'cur': order, 'form': form, 'data': data}
        paramstr = """?exchange=""" + exchange + '&ticker=' + ticker + '&order=' + order
        context['params'] = paramstr
        if page_num > 1:
            context['prev_exists'] = True
            context['prev'] = page_num - 1
        if page_num < tot_pgs:
            context['next_exists'] = True
            context['next'] = page_num + 1
        return render(request, f'{user_type}/stocklist.html', context)


def analysis_view(request, sid=0, eid=0):
    user_type = 'client' if is_client(request) else 'broker'
    if sid <= 0:
        stock = models.Stock.objects.all().first()
        sid = stock.sid
    else:
        stock = models.Stock.objects.get(sid=sid)
    if eid <= 0:
        exchange = models.ListedAt.objects.select_related('eid').filter(sid=stock).first().eid
        eid = exchange.eid
    else:
        exchange = models.Exchange.objects.get(eid=eid)
    # ph = custom_query("""
    #     SELECT price, creation_time FROM market_StockPricehistory as ph 
    #     WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])
    # price = [d['price'] for d in ph]
    # tsz = [d['creation_time'] for d in ph]
    # dates = matplotlib.dates.date2num(tsz)
    # fig = plt.figure(figsize=(16, 8))
    # plt.plot_date(dates, price, linestyle='solid', marker='None')
    # plt.title(f'{stock.ticker} Price at {exchange.name} Exchange')
    # plt.ylabel('Price')
    # plt.xlabel('Date')
    # buf = StringIO()
    # fig.savefig(buf, bbox_inches='tight', format='svg')
    # buf.seek(0)
    # plt.close()
    # return render(request, 'analysis.html', {'data': buf.getvalue()})
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])
    mv = custom_query("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS closing_price as 
        select time_bucket('1 day', creation_time) date, sid, eid, last(price, creation_time) AS price
        from market_StockPricehistory group by date, sid, eid with no data;""")
    ref = custom_query("""
        refresh materialized view closing_price;""")# refresh
    cp = custom_query("""
        SELECT date, price from closing_price where eid=%s and sid=%s;""", [eid, sid])
    ma = custom_query("""
        SELECT time_bucket('5 days', date) as date, avg(price) as price from closing_price where eid=%s and sid=%s group by eid, sid, date;""", [eid, sid])#moving avg
    ma2 = custom_query("""
        SELECT time_bucket('10 days', date) as date, avg(price) as price from closing_price where eid=%s and sid=%s group by eid, sid, date;""", [eid, sid])#moving avg
    # dr = custom_query("""
    #     SELECT date, ticker, eid, ((price/lag(price,1) over (partition by (ticker, eid) order by date)) from closing_price""")#daily return
    # dict_ph = [{'x': d['creation_time'], 'y': d['price']} for d in ph]
    price = [float(d['price']) for d in ph]
    tsz = [d['creation_time'] for d in ph]
    print(price)
    print(tsz)
    dates = matplotlib.dates.date2num(tsz)
    print(dates)
    plt.close()
    fig = plt.gcf()
    plt.plot_date(dates, price)
    plt.xlabel('time')
    plt.ylabel('price')
    fig.suptitle('Price vs Time')
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    graphic = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + urllib.parse.quote(graphic)

    price = [float(d['price']) for d in cp]
    tsz = [d['date'] for d in cp]
    print(price)
    print(tsz)
    dates = matplotlib.dates.date2num(tsz)
    print(dates)
    plt.close()
    fig = plt.gcf()
    plt.plot_date(dates, price)
    plt.xlabel('date')
    plt.ylabel('closing price')
    fig.suptitle('Closing Price')
    buf1 = BytesIO()
    fig.savefig(buf1, format='png')
    buf1.seek(0)
    graphic1 = base64.b64encode(buf1.read())
    uri1 = 'data:image/png;base64,' + urllib.parse.quote(graphic1)

    price = [float(d['price']) for d in ma]
    tsz = [d['date'] for d in ma]
    print(price)
    print(tsz)
    dates = matplotlib.dates.date2num(tsz)
    print(dates)
    plt.close()
    fig = plt.gcf()
    plt.plot_date(dates, price)
    plt.xlabel('date')
    plt.ylabel('clsing price')
    fig.suptitle('Closing Price (Moving average: 5days)')
    buf2 = BytesIO()
    fig.savefig(buf2, format='png')
    buf2.seek(0)
    graphic2 = base64.b64encode(buf2.read())
    uri2 = 'data:image/png;base64,' + urllib.parse.quote(graphic2)

    price = [float(d['price']) for d in ma2]
    tsz = [d['date'] for d in ma2]
    print(price)
    print(tsz)
    dates = matplotlib.dates.date2num(tsz)
    print(dates)
    plt.close()
    fig = plt.gcf()
    plt.plot_date(dates, price)
    plt.xlabel('date')
    plt.ylabel('closing price')
    fig.suptitle('Closing Price (Moving average: 10days)')
    buf3 = BytesIO()
    fig.savefig(buf3, format='png')
    buf3.seek(0)
    graphic3 = base64.b64encode(buf3.read())
    uri3 = 'data:image/png;base64,' + urllib.parse.quote(graphic3)

    return render(request, f'{user_type}/analysis.html', {'data': uri, 'cp': uri1, 'ma': uri2, 'ma1': uri3})
