from django.shortcuts import render as django_render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Value
from operator import itemgetter
from market.forms import *
from io import BytesIO, StringIO
import base64, urllib
import numpy as np
from django.core.serializers.json import DjangoJSONEncoder
from . import models
import random
import requests
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
    ph = custom_query("""
        SELECT price, creation_time FROM market_StockPricehistory as ph 
        WHERE ph.eid=%s and ph.sid=%s ORDER BY creation_time;""", [eid, sid])
    price = [d['price'] for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    fig = plt.figure(figsize=(16, 8))
    plt.plot_date(dates, price, linestyle='solid', marker='None')
    plt.title(f'{stock.ticker} Price at {exchange.name} Exchange')
    plt.ylabel('Price')
    plt.xlabel('Date')
    user = get_user_type(request)
    if user == 'admin/':
        return render(request, 'forbidden.html', {})
    return render(request, f'{user}analysis.html', {'data': get_svg(fig)})
