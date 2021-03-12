from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import sm.forms as allforms
import sm.models as allmodels
from django.db import connection
from operator import itemgetter
from io import BytesIO
import base64, urllib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
# Create your views here.
def index(request):
	return render(request, 'index.html', {})
    # return HttpResponse("You're at the stockmarket index.")

def dictfetchall(cursor): 
    "Returns all rows from a cursor as a dict" 
    desc = cursor.description 
    return [
            dict(zip([col[0] for col in desc], row)) 
            for row in cursor.fetchall() 
    ]

def clientsignup(request):
    if request.method == 'POST':
        form = allforms.SignUpForm(request.POST)
        if form.is_valid():
            user = allmodels.Person(name=form.cleaned_data.get('name'),address=form.cleaned_data.get('address'),telephone=form.cleaned_data.get('telephone'))
            # user.refresh_from_db()  # load the profile instance created by the signal
            user.save()
            # print(user.id,end='****\n')
            client=allmodels.Client(id=user,email=form.cleaned_data.get('email'))
            client.save()
            ac=allmodels.BankAccount(account_number=form.cleaned_data.get('account_number'),clid=client,balance=5)
            ac.save()
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=user.username, password=raw_password)
            # login(request, user)
            # return redirect('home')
    else:
        form = allforms.SignUpForm()
    return render(request, 'client_signup.html', {'form': form})

def brokersignup(request):
    if request.method == 'POST':
        form = allforms.SignUpForm_Broker(request.POST)
        if form.is_valid():
            user = allmodels.Person(name=form.cleaned_data.get('name'),address=form.cleaned_data.get('address'),telephone=form.cleaned_data.get('telephone'))
            # user.refresh_from_db()  # load the profile instance created by the signal
            user.save()
            # print(user.id,end='****\n')
            broker=allmodels.Broker(id=user,commission=form.cleaned_data.get('commission'),latency=form.cleaned_data.get('latency'))
            broker.save()
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=user.username, password=raw_password)
            # login(request, user)
            # return redirect('home')
            return HttpResponseRedirect('/sm/')
    else:
        form = allforms.SignUpForm_Broker()
    return render(request, 'broker_signup.html', {'form': form})


def stockList(request):
    def req_join():
        with connection.cursor() as cursor:
            cursor.execute("SELECT ticker, name, J1.eid as id, (SELECT price FROM sm_Pricehistory as ph WHERE ph.eid=J1.eid and ph.ticker=ticker ORDER BY creation_time DESC LIMIT 1) as latestprice FROM (sm_Listedat join sm_Stock using(ticker)) as J1 join sm_Exchange on (J1.eid=sm_exchange.id) order by ticker;")
            # cursor.execute("SELECT foo FROM bar WHERE baz = %s", [self.baz])
            row = dictfetchall(cursor)
        return row
    StockLt=req_join()
    if request.method == 'POST':
        form=allforms.SorterForm(request.POST)
        context={'cur':'Ticker', 'form':form,'data':StockLt}
        if form.is_valid() and 'sfilt' in request.POST:
            context['cur']=form.cleaned_data['sortfield'] #string of number
            tick=form.cleaned_data['ticker']
            exc=form.cleaned_data['exchange']
            data=StockLt
            if len(tick)!=0:
                data = [d for d in data if d['ticker']==tick]
            if len(exc)!=0:
                data = [d for d in data if d['name']==exc]
            if context['cur']=='Exchange':
                data = sorted(data, key=itemgetter('name'))
            elif context['cur']=='Latest Price':
                data = sorted(data, key=itemgetter('latestprice'))
            context['data']=data
        return render(request, 'stocklist.html', context)
    else:
        form=allforms.SorterForm()
        data=StockLt
        context={'cur':'Ticker', 'form':form,'data':data}
        return render(request, 'stocklist.html', context)

def analysis(request, tick, eid):
    def req_join():
        with connection.cursor() as cursor:
            cursor.execute("SELECT price, creation_time FROM sm_Pricehistory as ph WHERE ph.eid=%s and ph.ticker=%s ORDER BY creation_time;", [eid, tick])
            # cursor.execute("SELECT foo FROM bar WHERE baz = %s", [self.baz])
            row = dictfetchall(cursor)
        return row

    ph = req_join()
    price = [d['price'] for d in ph]
    tsz = [d['creation_time'] for d in ph]
    dates = matplotlib.dates.date2num(tsz)
    print(dates)
    print(price)
    # plt.figure(figsize=(32,18))
    plt.plot_date(dates, price)
    # plt.show()
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    # # image_png = buf.getvalue()
    # # buf.close()

    graphic = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + urllib.parse.quote(graphic)
    # print(uri)
    return render(request, 'analysis.html', {'data': uri})

