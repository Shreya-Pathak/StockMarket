from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from operator import itemgetter
import market.forms as allforms
from io import BytesIO
import base64, urllib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Create your views here.


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


def stockList(request):
    def req_join():
        with connection.cursor() as cursor:
            cursor.execute("SELECT ticker, name, J1.eid as id, (SELECT price FROM market_Pricehistory as ph WHERE ph.eid=J1.eid and ph.ticker=ticker ORDER BY creation_time DESC LIMIT 1) as latestprice FROM (market_Listedat join market_Stock using(ticker)) as J1 join market_Exchange on (J1.eid=market_exchange.id) order by ticker;")
            row = dictfetchall(cursor)
        return row

    StockLt = req_join()
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
        return render(request, 'stocklist.html', context)
    else:
        form = allforms.SorterForm()
        data = StockLt
        context = {'cur': 'Ticker', 'form': form, 'data': data}
        return render(request, 'stocklist.html', context)


def analysis(request, tick, eid):
    def req_join():
        with connection.cursor() as cursor:
            cursor.execute("SELECT price, creation_time FROM market_Pricehistory as ph WHERE ph.eid=%s and ph.ticker=%s ORDER BY creation_time;", [eid, tick])
            row = dictfetchall(cursor)
        return row

    ph = req_join()
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
