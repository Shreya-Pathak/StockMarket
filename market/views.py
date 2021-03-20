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
from django.core.serializers.json import DjangoJSONEncoder


# Create your views here.
def index_view(request):
    return HttpResponseRedirect('stocklist')


def custom_query(query, format_vars=None):
    "executes ssql query and returns each row as a dict"
    if not query.endswith(';'):
        query += ';'
    with connection.cursor() as cursor:
        cursor.execute(query, format_vars)
        if not(cursor.description):
            return 
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return rows


def stocklist_view(request,client=0):
    StockLt = custom_query("""
    SELECT ticker, name, J1.eid AS id, sid,
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


def analysis_view(request, sid, eid, client=0):
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])

    # mv = custom_query("""
    #     CREATE MATERIALIZED VIEW IF NOT EXISTS closing_price AS WITH max_t 
    #     as (select time_bucket('1 day', creation_time) as date, max(creation_time) as creation_time, 
    #     ticker, eid from sm_pricehistory group by date, ticker, eid) select date, ticker, eid, price 
    #     from sm_pricehistory natural join max_t with no data;""")#create materialised view
    mv = custom_query("""
        CREATE materialized view if not exists closing_price as 
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
    plt.xticks(rotation=90)
    fig.suptitle('Price vs Time')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
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
    plt.xticks(rotation=90)
    fig.suptitle('Closing Price')
    buf1 = BytesIO()
    fig.savefig(buf1, format='png', bbox_inches='tight')
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
    plt.xticks(rotation=90)
    fig.suptitle('Closing Price (Moving average: 5days)')
    buf2 = BytesIO()
    fig.savefig(buf2, format='png', bbox_inches='tight')
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
    plt.xticks(rotation=90)
    fig.suptitle('Closing Price (Moving average: 10days)')
    buf3 = BytesIO()
    fig.savefig(buf3, format='png', bbox_inches='tight')
    buf3.seek(0)
    graphic3 = base64.b64encode(buf3.read())
    uri3 = 'data:image/png;base64,' + urllib.parse.quote(graphic3)

    if client==1:
        return render(request, 'client/analysis.html', {'data': uri, 'cp': uri1, 'ma': uri2, 'ma1': uri3})
    else:
        return render(request, 'broker/analysis.html', {'data': uri, 'cp': uri1, 'ma': uri2, 'ma1': uri3})