from django.shortcuts import render as django_render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count, F, Value
from operator import itemgetter
from market.forms import *
from io import BytesIO, StringIO
import base64, urllib
import numpy as np
from time import time
from django.core.serializers.json import DjangoJSONEncoder
from . import models
import random
import requests
import statistics as st
import datetime
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import matplotlib
matplotlib.use('Agg')
from matplotlib import style
style.use('ggplot')
import matplotlib.pyplot as plt


# Create your views here.
def check_type(v, t=int):
    try:
        return t(v)
    except:
        return None


def is_img(url):
    h = requests.head(url)
    t = h.headers.get('content-type')
    return ('image' in t)


def render(request, html_file, context={}):
    indices = list(models.Indices.objects.all())
    random.shuffle(indices)
    context.update(indices=indices)
    return django_render(request, html_file, context)


def get_user_type(request):
    if request.user.is_authenticated:
        client = models.Client.objects.filter(username=request.user.username).first()
        if client is not None:
            return 'client/'
        broker = models.Broker.objects.filter(username=request.user.username).first()
        if broker is not None:
            return 'broker/'
        return 'admin/'
    return ''


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

def stocklist_initial(val):
    if val=='change':
        return 'Change'
    if val=='eid__name':
        return 'Exchange'
    if val=='last_price':
        return 'Last Price'
    else:
        return 'Ticker'

def stocklist_view(request, page_num=1):
    if request.method == 'POST':
        form = StockSorterForm(request.POST)
        if form.is_valid() and 'sfilt' in request.POST:
            sortfield = form.cleaned_data['sortfield']  #string of number
            ticker = form.cleaned_data['ticker']
            exchange = form.cleaned_data['exchange']
            if sortfield == 'Exchange':
                order = 'eid__name'
            elif sortfield == 'Latest Price':
                order = 'last_price'
            elif sortfield == 'Change':
                order = 'change'
            else:
                order = 'sid__ticker'
            paramstr = f'?exchange={exchange}&ticker={ticker}&order={order}'
            return redirect(f'/market/stocklist/1{paramstr}')
    exchange = request.GET.get('exchange', '')
    ticker = request.GET.get('ticker', '')
    order = request.GET.get('order', 'sid__ticker')
    paramstr = f'?exchange={exchange}&ticker={ticker}&order={order}'

    form = StockSorterForm()
    # print(order)
    form['sortfield'].initial = stocklist_initial(order) if order != 'sid__ticker' else 'Ticker'
    form['ticker'].initial=ticker
    form['exchange'].initial=exchange
    StockLt = models.ListedAt.objects.filter(sid__ticker__icontains=ticker, eid__name__icontains=exchange)
    StockLt = StockLt.select_related('sid', 'eid').order_by(order).all()
    pg = Paginator(StockLt, 8)
    tot_pgs = pg.num_pages
    page_num = min(max(page_num, 1), tot_pgs)
    StockLt = pg.page(page_num).object_list

    context = {'cur': order, 'form': form, 'data': StockLt, 'params': paramstr, 'pagestr': f'Page {page_num} of {tot_pgs}'}
    if page_num > 1:
        context['prev_exists'] = True
        context['prev'] = page_num - 1
    if page_num < tot_pgs:
        context['next_exists'] = True
        context['next'] = page_num + 1
    user = get_user_type(request)
    if user == 'client/':
        context.update(is_client=True)
    if user == 'admin/':
        return render(request, 'forbidden.html', {})
    return render(request, f'{user}stocklist.html', context)

def company_initial(val):
    if val=='name':
        return 'Name'
    if val=='country':
        return 'Country'
    else:
        return 'Ticker'

def companies_view(request, cid=0, page_num=1):
    company = models.Company.objects.select_related('cid').filter(pk=cid).first()
    if company is not None:
        if not is_img(company.logo):
            company.logo = 'https://logo.clearbit.com/clearbit.com'
        context = {'company': company, 'details': True}
    else:
        if request.method == 'POST':
            form = CompanySorterForm(request.POST)
            if form.is_valid() and 'cfilt' in request.POST:
                sf = form.cleaned_data['sortfield']  #string of number
                name = form.cleaned_data['name']
                country = form.cleaned_data['country']
                sector = form.cleaned_data['sector']
                if sf == 'Name':
                    order = 'name'
                elif sf == 'Country':
                    order = 'country'
                else:
                    order = 'cid__ticker'
                paramstr = f'?name={name}&country={country}&sector={sector}&order={order}'
                return redirect(f'/market/companies/0/1{paramstr}')
        name = request.GET.get('name', '')
        country = request.GET.get('country', '')
        sector = request.GET.get('sector', '')
        order = request.GET.get('order', 'cid__ticker')
        paramstr = f'?name={name}&country={country}&sector={sector}&order={order}'
        # print(order)
        form = CompanySorterForm()
        form['sortfield'].initial = company_initial(order)  if order != 'cid__ticker' else 'Ticker'
        form['name'].initial=name
        form['country'].initial=country
        form['sector'].initial=sector
        companies = models.Company.objects.filter(name__icontains=name, country__icontains=country, sector__icontains=sector)
        companies = companies.select_related('cid').order_by(order).all()
        pg = Paginator(companies, 8)
        tot_pgs = pg.num_pages
        page_num = min(max(page_num, 1), tot_pgs)
        companies = pg.page(page_num).object_list

        context = {'cur': order, 'form': form, 'data': companies, 'params': paramstr, 'details': False, 'pagestr': f'Page {page_num} of {tot_pgs}'}
        if page_num > 1:
            context['prev_exists'] = True
            context['prev'] = page_num - 1
        if page_num < tot_pgs:
            context['next_exists'] = True
            context['next'] = page_num + 1
    user = get_user_type(request)
    if user == 'admin/':
        return render(request, 'forbidden.html', {})
    return render(request, f'{user}companies.html', context)


def add_funds_view(request):
    user_type = get_user_type(request)
    if user_type in ['', 'admin/']:
        return render(request, 'forbidden.html', {})
    if user_type == 'broker/':
        user_user = models.Broker.objects.filter(username=request.user.username).first()
        user = user_user.bid
    else:
        user_user = models.Client.objects.filter(username=request.user.username).first()
        user = user_user.clid
    
    acct_no = check_type(request.GET.get('to_remove', None), int)
    if acct_no is not None:
        acct = models.BankAccount.objects.filter(account_number=acct_no, pid=user).first()
        if acct is not None:
            acct.delete()
            messages.success(request, 'Account removed.')
        else:
            messages.error(request, 'This account is not yours to remove.')
        return HttpResponseRedirect('add_funds')

    form = AddAcctForm()
    if request.method == 'POST':
        if request.POST['submit'] == 'add_funds':
            funds = check_type(request.POST['funds'], int)
            acct_no = check_type(request.POST['acct'], int)
            if funds is None or acct_no is None:
                messages.error(request, 'Invalid request.')
            else:
                acct = models.BankAccount.objects.filter(account_number=acct_no, pid=user).first()
                if acct is None:
                    messages.error(request, "You can't add funds from others' account.")
                elif acct.balance < funds:
                    messages.error(request, "Insufficient Funds in your bank account.")
                else:
                    with transaction.atomic():    
                        acct.balance -= funds
                        user_user.balance += funds
                        acct.save()
                        user_user.save()
                    messages.success(request, "Funds added to your wallet.")
        else:
            form = AddAcctForm(request.POST) 
            if form.is_valid():
                acct_no = form.cleaned_data['acct_no']
                name = form.cleaned_data['name']
                balance = form.cleaned_data['balance']
                acct = models.BankAccount.objects.filter(account_number=acct_no).first()
                if acct is None:
                    acct = models.BankAccount(account_number=acct_no, bank_name=name, pid=user, balance=balance)
                    acct.save()
                    messages.success(request, 'Bank Account created.')
                else:
                    messages.error(request, 'This bank account already exists.')
    accts = models.BankAccount.objects.filter(pid=user)
    return render(request, f'{user_type}add_funds.html', {'form':form, 'accts':accts})


def withdraw_view(request):
    user_type = get_user_type(request)
    if user_type in ['', 'admin/']:
        return render(request, 'forbidden.html', {})
    if user_type == 'broker/':
        user_user = models.Broker.objects.filter(username=request.user.username).first()
        user = user_user.bid
    else:
        user_user = models.Client.objects.filter(username=request.user.username).first()
        user = user_user.clid
    if request.method == 'POST':
        if request.POST['submit'] == 'withdraw':
            funds = check_type(request.POST['funds'], int)
            acct_no = check_type(request.POST['acct'], int)
            if funds is None or acct_no is None:
                messages.error(request, 'Invalid request.')
            else:
                acct = models.BankAccount.objects.filter(account_number=acct_no, pid=user).first()
                if acct is None:
                    messages.error(request, "You can't deposit funds to others' account.")
                elif user_user.balance < funds:
                    messages.error(request, "Insufficient Funds in your wallet.")
                else:
                    with transaction.atomic():    
                        user_user.balance -= funds
                        acct.balance += funds
                        acct.save()
                        user_user.save()
                    messages.success(request, "Funds added to your bank account.")
    accts = models.BankAccount.objects.filter(pid=user)
    return render(request, f'{user_type}withdraw.html', {'accts':accts})


def get_svg(fig):
    buf = BytesIO()
    fig.savefig(buf, bbox_inches='tight', format='svg')
    buf.seek(0)
    graphic = base64.b64encode(buf.read())
    buf.close()
    plt.close()
    uri = 'data:image/svg+xml;base64,' + urllib.parse.quote(graphic)
    return uri


def analysis_view(request, sid=0, eid=0):
    user = get_user_type(request)
    if user == 'admin/':
        return render(request, 'forbidden.html', {})
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

    print(sid, eid)
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])

    cp = custom_query("""
        SELECT date, price from closing_price where eid=%s and sid=%s;""", [eid, sid])

    ma = custom_query("""
        SELECT time_bucket('3 days', date) as date1, avg(price) as price from closing_price where eid=%s and sid=%s group by date1 order by date1;""", [eid, sid])#moving avg

    ma2 = custom_query("""
        SELECT time_bucket('5 days', date) as date1, avg(price) as price from closing_price where eid=%s and sid=%s group by date1 order by date1;""", [eid, sid])#moving avg

    dr = custom_query("""
        SELECT date, dr from daily_return where eid=%s and sid=%s;""", [eid, sid])
    # dr = custom_query("""
    #     SELECT date, ((price/lag(price, 1) over (partition by (sid, eid) order by date))-1) dr from closing_price where eid=%s and sid=%s;""", [eid, sid])#daily return
    # dict_ph = [{'x': d['creation_time'], 'y': d['price']} for d in ph]
    
    price = [float(d['price']) for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    fig = plt.figure(figsize=(6, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.title(f'{stock.ticker} Price at {exchange.name} Exchange')
    plt.ylabel('Price (in $)')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf = StringIO()
    fig.savefig(buf, bbox_inches='tight', format='svg', transparent=True)
    buf.seek(0)
    plt.close()

    price1 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
    tsz = [d['date'] for d in dr]
    dates = matplotlib.dates.date2num(tsz)
    fig4 = plt.figure(figsize=(6, 4))
    plt.plot_date(dates, price1, linestyle='solid', marker='None')
    plt.title(f'{stock.ticker} Daily Return (in %) at {exchange.name} Exchange')
    plt.ylabel('Daily Return')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf4 = StringIO()
    fig4.savefig(buf4, bbox_inches='tight', format='svg', transparent=True)
    buf4.seek(0)
    plt.close()

    mean = 0 if len(price1)==0 else "{0:0.3f}".format(st.mean(price1))
    std = 0 if len(price1)<=1 else "{0:0.3f}".format(st.stdev(price1))

    price_ = [float(d['price']) for d in cp]
    tsz_ = [d['date'] for d in cp]
    dates_ = matplotlib.dates.date2num(tsz_)
    fig1 = plt.figure(figsize=(6, 4))
    plt.plot_date(dates_, price_, linestyle='solid', marker='None')
    price = [float(d['price']) for d in ma]
    tsz = [d['date1'] for d in ma]
    dates = matplotlib.dates.date2num(tsz)
    # fig2 = plt.figure(figsize=(8, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    price = [float(d['price']) for d in ma2]
    tsz = [d['date1'] for d in ma2]
    dates = matplotlib.dates.date2num(tsz)
    # fig3 = plt.figure(figsize=(8, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.legend(['Closing Price', 'MA over 3 days', 'MA over 5 days'])
    plt.title(f'{stock.ticker} Closing Price at {exchange.name} Exchange')
    plt.ylabel('Closing Price (in $)')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf1 = StringIO()
    fig1.savefig(buf1, bbox_inches='tight', format='svg', transparent=True)
    buf1.seek(0)
    plt.close()

    b1 = False
    x1 = ""
    if len(price_)>1:
        b1 = True
        t1 = time()
        model = ARIMA(price_, order=(6, 0, 2))
        model_fit = model.fit()
        yhat = model_fit.predict(len(price_)+1, len(price_)+30, typ='levels')
        t2 = time()
        print(t2-t1)
        print(len(yhat))
        # rms = sqrt(mean_squared_error(pr, yhat[:-100]))
        # print(rms)
        x = [tsz_[-1] + datetime.timedelta(days=i) for i in range(30)]
        figq = plt.figure(figsize=(15, 5))
        # x = np.append(tsz_, x)
        dates_1 = matplotlib.dates.date2num(x)
        plt.plot_date(dates_, price_, linestyle='solid', marker='None', color='black')
        plt.plot_date(dates_1, yhat, linestyle='solid', marker='None', color='red')
        # plt.legend('Predicted Closing Price')
        plt.title(f'Predicted {stock.ticker} Closing Price at {exchange.name} Exchange')
        plt.ylabel('Closing Price (in $)')
        plt.xlabel('Date')
        plt.xticks(rotation=90)
        bufq = StringIO()
        figq.savefig(bufq, bbox_inches='tight', format='svg', transparent=True)
        bufq.seek(0)
        plt.close()
        x1 = bufq.getvalue()
    else:
        x1 = 0
        messages.info(request, 'Too few points for prediction.')

    form = OrderForm()
    # dform = dateForm()
    if request.method == 'POST':
        print(request.POST)
        form = OrderForm(data=request.POST)
        if form.is_valid():
            print("here")
            cors = form.cleaned_data['stock']
            core = form.cleaned_data['exchange']
            cr = custom_query("""select d1.dr as dr1,d2.dr as dr2 from (select date, dr from daily_return where eid=%s and sid=%s) as d1 join (select date, dr from daily_return where eid=%s and sid=%s) d2 using(date);""", [eid, sid, core.eid, cors.sid])
            dr1 = [0 if d['dr1'] is None else float(d['dr1']) for d in cr]
            dr2 = [0 if d['dr2'] is None else float(d['dr2']) for d in cr]
            fig5 = plt.figure(figsize=(6, 4))
            plt.scatter(dr1, dr2, c='red')
            plt.title(f'Correlation btw {stock.ticker} at {exchange.name} and {cors.ticker} at {core.name}')
            plt.ylabel(f'{cors.ticker} at {core.name}')
            plt.xlabel(f'{stock.ticker} at {exchange.name}')
            buf5 = StringIO()
            fig5.savefig(buf5, bbox_inches='tight', format='svg', transparent=True)
            buf5.seek(0)
            plt.close()
            corr_v = np.corrcoef(dr1,dr2)[0][1]
            corr_v = "{0:0.2f}".format(corr_v)
            return render(request, f'{user}analysis.html', {'st':stock.ticker, 'ex':exchange.name, 'mean':mean, 'risk':std, 'data': buf.getvalue(), 'cp': buf1.getvalue(),  'dr':buf4.getvalue(), 'form':form, 'cimage':buf5.getvalue(), 'corrv':corr_v, 'pred': x1, 'b1':b1})
        elif 'datepick' in request.POST:
            start_date=request.POST.get('start','')
            end_date=request.POST.get('end','')
            #please add redirect here and params to request

    # else:
    form = OrderForm()
    
    dr1 = []
    dr1 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
    dr2 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
    fig5 = plt.figure(figsize=(6, 4))
    plt.scatter(dr1, dr2, c='red')
    plt.title(f'Correlation btw {stock.ticker} at {exchange.name} and {stock.ticker} at {exchange.name}')
    plt.ylabel(f'{stock.ticker} at {exchange.name}')
    plt.xlabel(f'{stock.ticker} at {exchange.name}')
    buf5 = StringIO()
    fig5.savefig(buf5, bbox_inches='tight', format='svg', transparent=True)
    buf5.seek(0)
    plt.close()
    corr_v = np.corrcoef(dr1,dr2)[0][1]
    corr_v = "{0:0.2f}".format(corr_v)
    return render(request, f'{user}analysis.html', {'st':stock.ticker, 'ex':exchange.name, 'mean':mean, 'risk':std, 'data': buf.getvalue(), 'cp': buf1.getvalue(),  'dr':buf4.getvalue(), 'form':form, 'cimage':buf5.getvalue(), 'corrv':corr_v, 'pred': x1, 'b1':b1})


def analysis_view_index(request, iid=0):
    user = get_user_type(request)
    if user == 'admin/':
        return render(request, 'forbidden.html', {})
    if iid <= 0:
        index = models.Indices.objects.all().first()
        iid = index.iid
    else:
        index = models.Indices.objects.get(iid=iid)

    t1 = time()
    
    ph = custom_query("""
        SELECT price, creation_time FROM market_IndexPricehistory as ph WHERE ph.iid=%s ORDER BY creation_time;""", [iid])

    cp = custom_query("""
        SELECT date, price from closing_price_ind where iid=%s order by date;""", [iid])

    ma = custom_query("""
        SELECT time_bucket('20 days', date) as date1, avg(price) as price from closing_price_ind where iid=%s group by date1 order by date1;""", [iid])#moving avg

    ma2 = custom_query("""
        SELECT time_bucket('40 days', date) as date1, avg(price) as price from closing_price_ind where iid=%s group by date1 order by date1;""", [iid])#moving avg

    dr = custom_query("""
        SELECT date, dr from daily_return_ind where iid=%s;""", [iid])
    # dr = custom_query("""
    #     SELECT date, ((price/lag(price, 1) over (partition by (sid, eid) order by date))-1) dr from closing_price where eid=%s and sid=%s;""", [eid, sid])#daily return
    # dict_ph = [{'x': d['creation_time'], 'y': d['price']} for d in ph]
    
    t2 = time()
    print(t2-t1)

    price = [float(d['price']) for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    fig = plt.figure(figsize=(6, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.title(f'{index.index_name} Price')
    plt.ylabel('Price')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf = StringIO()
    fig.savefig(buf, bbox_inches='tight', format='svg', transparent=True)
    buf.seek(0)
    plt.close()

    price1 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
    tsz = [d['date'] for d in dr]
    dates = matplotlib.dates.date2num(tsz)
    fig4 = plt.figure(figsize=(6, 4))
    plt.plot_date(dates, price1, linestyle='solid', marker='None')
    plt.title(f'{index.index_name} Daily Return (in %)')
    plt.ylabel('Daily Return')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf4 = StringIO()
    fig4.savefig(buf4, bbox_inches='tight', format='svg', transparent=True)
    buf4.seek(0)
    plt.close()

    mean = 0 if len(price1)==0 else "{0:0.3f}".format(st.mean(price1))
    std = 0 if len(price1)<=1 else "{0:0.3f}".format(st.stdev(price1))

    price_ = [float(d['price']) for d in cp]
    tsz_ = [d['date'] for d in cp]
    dates_ = matplotlib.dates.date2num(tsz_)
    fig1 = plt.figure(figsize=(6, 4))
    plt.plot_date(dates_, price_, linestyle='solid', marker='None')
    price = [float(d['price']) for d in ma]
    tsz = [d['date1'] for d in ma]
    dates = matplotlib.dates.date2num(tsz)
    # fig2 = plt.figure(figsize=(8, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    price = [float(d['price']) for d in ma2]
    tsz = [d['date1'] for d in ma2]
    dates = matplotlib.dates.date2num(tsz)
    # fig3 = plt.figure(figsize=(8, 4))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.legend(['Closing Price', 'MA over 20 days', 'MA over 40 days'])
    plt.title(f'{index.index_name} Closing Price')
    plt.ylabel('Closing Price')
    plt.xlabel('Date')
    plt.xticks(rotation=90)
    buf1 = StringIO()
    fig1.savefig(buf1, bbox_inches='tight', format='svg', transparent=True)
    buf1.seek(0)
    plt.close()

    # df = pd.DataFrame(price_, index=tsz_, columns=['price'])
    # t1 = time()
    # model = ARIMA(price_, order=(4, 0, 1))
    # model_fit = model.fit()
    # yhat = model_fit.predict(len(price_)+1, len(price_)+500, typ='levels')
    # t2 = time()
    # print(t2-t1)
    # print(len(yhat))
    # # rms = sqrt(mean_squared_error(pr, yhat[:-100]))
    # # print(rms)
    # x = [tsz_[-1] + datetime.timedelta(days=i) for i in range(500)]
    # figq = plt.figure(figsize=(15, 5))
    # # x = np.append(tsz_, x)
    # dates_1 = matplotlib.dates.date2num(x)
    # plt.plot_date(dates_, price_, linestyle='solid', marker='None', color='black')
    # plt.plot_date(dates_1, yhat, linestyle='solid', marker='None', color='red')
    # # plt.legend('Predicted Closing Price')
    # plt.title(f'{index.index_name} Predicted Closing Price')
    # plt.ylabel('Closing Price')
    # plt.xlabel('Date')
    # plt.xticks(rotation=90)
    # bufq = StringIO()
    # figq.savefig(bufq, bbox_inches='tight', format='svg', transparent=True)
    # bufq.seek(0)
    # plt.close()


    form = corrForm_ind()
    if request.method == 'POST':
        form = corrForm_ind(request.POST)
        if form.is_valid():
            cors = form.cleaned_data['index']
            # core = form.cleaned_data['corre']
            # print(cor.sid)
            cr = custom_query("""select d1.dr as dr1,d2.dr as dr2 from (select date, dr from daily_return_ind where iid=%s) as d1 join (select date, dr from daily_return_ind where iid=%s) d2 using(date);""", [iid, cors.iid])
            dr1 = [0 if d['dr1'] is None else float(d['dr1']) for d in cr]
            dr2 = [0 if d['dr2'] is None else float(d['dr2']) for d in cr]
            fig5 = plt.figure(figsize=(6, 4))
            plt.scatter(dr1, dr2, c='red')
            plt.title(f'Correlation btw {index.index_name} and {cors.index_name}')
            plt.ylabel(f'{cors.index_name}')
            plt.xlabel(f'{index.index_name}')
            buf5 = StringIO()
            fig5.savefig(buf5, bbox_inches='tight', format='svg', transparent=True)
            buf5.seek(0)
            plt.close()
            corr_v = np.corrcoef(dr1,dr2)[0][1]
            corr_v = "{0:0.2f}".format(corr_v)
            return render(request, f'{user}analysis_ind.html', {'st':index.index_name, 'mean':mean, 'risk':std, 'data': buf.getvalue(), 'cp': buf1.getvalue(),  'dr':buf4.getvalue(), 'form':form, 'cimage':buf5.getvalue(), 'corrv':corr_v})
    else:
        form = corrForm_ind()
        dr1 = []
        dr1 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
        dr2 = [0 if d['dr'] is None else float(d['dr']) for d in dr]
        fig5 = plt.figure(figsize=(6, 4))
        plt.scatter(dr1, dr2, c='red')
        plt.title(f'Correlation btw {index.index_name} and {index.index_name}')
        plt.ylabel(f'{index.index_name}')
        plt.xlabel(f'{index.index_name}')
        buf5 = StringIO()
        fig5.savefig(buf5, bbox_inches='tight', format='svg', transparent=True)
        buf5.seek(0)
        plt.close()
        corr_v = np.corrcoef(dr1,dr2)[0][1]
        corr_v = "{0:0.2f}".format(corr_v)
        return render(request, f'{user}analysis_ind.html', {'st':index.index_name, 'mean':mean, 'risk':std, 'data': buf.getvalue(), 'cp': buf1.getvalue(),  'dr':buf4.getvalue(), 'form':form, 'cimage':buf5.getvalue(), 'corrv':corr_v})