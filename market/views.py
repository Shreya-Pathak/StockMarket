from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from django.contrib.auth.decorators import login_required
from operator import itemgetter
import market.forms as allforms
from io import BytesIO
import base64, urllib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


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


def stocklist_view(request,client=0):
    StockLt = custom_query("""
    SELECT ticker, name, J1.eid AS id,
    (SELECT price FROM market_StockPriceHistory AS ph
    WHERE ph.eid = J1.eid AND ph.sid = sid
    ORDER BY creation_time DESC LIMIT 1) AS latestprice
    FROM (market_ListedAt JOIN market_Stock USING (sid)) AS J1
    JOIN market_Exchange ON (J1.eid = market_exchange.eid)
    ORDER BY ticker;""")

    if request.method == 'POST':
        form = allforms.SorterForm(request.POST)
        context = {'cur': 'Ticker', 'form': form, 'data': StockLt}
        if form.is_valid() and 'sfilt' in request.POST:
            context['cur'] = form.cleaned_data['sortfield']  #string of number
            tick = form.cleaned_data['ticker']
            exc = form.cleaned_data['exchange']
            data = StockLt
            if len(tick) != 0:
                data = [d for d in data if d['ticker'] == tick]
            if len(exc) != 0:
                data = [d for d in data if d['name'] == exc]
            if context['cur'] == 'Exchange':
                data = sorted(data, key=itemgetter('name'))
            elif context['cur'] == 'Latest Price':
                data = sorted(data, key=itemgetter('latestprice'))
            context['data'] = data
            if client==0:
                return render(request, 'broker/stocklist.html', context)
            else:
                return render(request, 'client/stocklist.html', context)
    else:
        form = allforms.SorterForm()
        data = StockLt
        context = {'cur': 'Ticker', 'form': form, 'data': data}
        if client==0:
            return render(request, 'broker/stocklist.html', context)
        else:
            return render(request, 'client/stocklist.html', context)


def analysis_view(request, sid, eid):
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])
    
    price = [d['price'] for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    plt.plot_date(dates, price)
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    graphic = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + urllib.parse.quote(graphic)
    return render(request, 'analysis.html', {'data': uri})