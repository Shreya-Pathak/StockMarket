from django.shortcuts import render, redirect
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
from . import models

import matplotlib
matplotlib.use('Agg')
from matplotlib import style
style.use('ggplot')
import matplotlib.pyplot as plt


# Create your views here.
def index_view(request):
    return HttpResponseRedirect('stocklist')


def custom_query(query, format_vars=None):
    "executes ssql query and returns each row as a dict"
    if not query.endswith(';'):
        query += ';'
    with connection.cursor() as cursor:
        cursor.execute(query, format_vars)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows


def stocklist_view(request, client=0, st=0):
    PGSZ = 8
    exchange = request.GET.get('exchange', '')
    ticker = request.GET.get('ticker', '')
    order = request.GET.get('order', 'sid__ticker')
    if st == 0:
        st += 1
    # StockLt = custom_query("""
    # SELECT sid,ticker, name, J1.eid AS id,
    # (SELECT price FROM market_StockPriceHistory AS ph
    # WHERE ph.eid = J1.eid AND ph.sid = sid"""+
    # """ ORDER BY creation_time DESC LIMIT 1) AS latestprice
    # FROM (market_ListedAt JOIN market_Stock USING (sid)) AS J1
    # JOIN market_Exchange ON (J1.eid = market_exchange.eid) WHERE """+ """name ilike '%"""+exchange+"""%' AND ticker ilike  '%"""+ticker
    # +"""%' ORDER BY """+
    #  order + """ OFFSET """+str(st*PGSZ)+""" LIMIT """+str(PGSZ+1)+""" ;""")
    # StockLt = custom_query("""
    # CREATE VIEW if not exists stocklists SELECT sid,ticker, name, J1.eid AS id,
    # (SELECT price FROM market_StockPriceHistory AS ph
    # WHERE ph.eid = J1.eid AND ph.sid = sid"""+
    # """ ORDER BY creation_time DESC LIMIT 1) AS latestprice
    # FROM (market_ListedAt JOIN market_Stock USING (sid)) AS J1
    # JOIN market_Exchange ON (J1.eid = market_exchange.eid); """)
    # if len(StockLt)!=PGSZ+1:
    #     last=True
    # else:
    #     last=False
    #     StockLt=StockLt[:-1]
    StockLt = models.Stocklists.objects.filter(sid__ticker__icontains=ticker, eid__name__icontains=exchange)
    StockLt = StockLt.select_related('sid', 'eid').order_by(order).all()
    pg = Paginator(StockLt, PGSZ)
    StockLt = pg.page(st).object_list
    tot_pgs = pg.num_pages
    if request.method == 'POST':
        form = allforms.SorterForm(request.POST)
        if form.is_valid() and 'sfilt' in request.POST:
            sf = form.cleaned_data['sortfield']  #string of number
            tick = form.cleaned_data['ticker']
            exc = form.cleaned_data['exchange']
            data = StockLt
            order = 'ticker'
            if sf == 'Exchange':
                order = 'eid__name'
            elif sf == 'Latest Price':
                order = 'last_price'
            return redirect(f'/market/stocklist/{client}/1/?exchange=' + exc + '&ticker=' + tick + '&order=' + order)
    else:
        form = allforms.SorterForm()
        form['sortfield'].initial='Ticker' if order=='ticker' else ('Exchange' if order=='name' else 'Latest Price')
        data = StockLt
        context = {'cur': order, 'form': form, 'data': data}
        paramstr = """?exchange=""" + exchange + '&ticker=' + ticker + '&order=' + order
        context['params'] = paramstr
        if st > 1:
            context['prev_exists'] = True
            context['prev'] = st - 1
        if st < tot_pgs:
            context['next_exists'] = True
            context['next'] = st + 1
        if client == 0:
            return render(request, 'broker/stocklist.html', context)
        else:
            return render(request, 'client/stocklist.html', context)


def analysis_view(request, sid, eid):
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])
    stock = models.Stock.objects.get(sid=sid)
    exchange = models.Exchange.objects.get(eid=eid)
    price = [d['price'] for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    fig = plt.figure(figsize=(16, 8))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.title(f'{stock.ticker} Price at {exchange.name} Exchange')
    plt.ylabel('Price')
    plt.xlabel('Date')
    buf = StringIO()
    fig.savefig(buf, bbox_inches='tight', format='svg')
    buf.seek(0)
    plt.close()
    return render(request, 'analysis.html', {'data': buf.getvalue()})
