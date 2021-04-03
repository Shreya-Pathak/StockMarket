from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
import client.forms as forms
import market.models as models
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

# Create your views here.


def get_client(username):
    client = None
    try:
        client = models.Client.objects.get(username=username)
    except Exception as e:
        pass
    return client


def check_user(request):
    if not request.user.is_authenticated:
        return False
    if get_client(request.user.username) is None:
        messages.warning(request, 'You do not have access to this page.')
        return True
    return False


def index_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    else:
        return HttpResponseRedirect('login')


def signup_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        messages.info(request, 'Please logout first.')
        return HttpResponseRedirect('home')
    if request.method == 'POST':
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email')
            address = form.cleaned_data.get('address')
            telephone = form.cleaned_data.get('telephone')
            password = form.cleaned_data.get('password')
            username = email.split('@')[0]
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
                user.save()
                person = models.Person(name=name, address=address, telephone=telephone)
                person.save()
                client = models.Client(clid=person, username=username, balance=0)
                client.save()
                messages.info(request, 'You can now login using your new account.')
                return HttpResponseRedirect('login')
            messages.error(request, "Username already exists.")
    else:
        form = forms.SignUpForm()
    return render(request, 'client/signup.html', {'form': form})


def login_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return HttpResponseRedirect('home')
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if get_client(username) is None:
                messages.warning(request, 'You can\'t login as a client.')
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.info(request, 'Successfully logged in.')
                    return HttpResponseRedirect('home')
                messages.error(request, 'Wrong username/password.')
    else:
        form = forms.LoginForm()
    return render(request, 'client/login.html', {'form': form})


def logout_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Successfully logged out.')
    return HttpResponseRedirect('login')


def home_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('login')
    return render(request, 'client/home.html')


def portfolio_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('login')
    client = get_client(request.user.username)
    assert client is not None
    if request.method == 'POST':
        formdata = forms.PortfolioForm(request.POST)
        if formdata.is_valid():
            newname = formdata.cleaned_data['pname']
            if models.Portfolio.objects.filter(pname=newname, clid=client).exists():
                messages.error(request, "Portfolio already exists.")
                return HttpResponseRedirect('portfolio')
            new_portfolio = models.Portfolio(pname=newname, clid=client)
            new_portfolio.save()
    all_folios = models.Portfolio.objects.all().filter(clid=client).order_by('pname')
    data = {}
    for i in all_folios:
        stock_folio = models.Holdings.objects.filter(folio_id_id=i.folio_id)
        stock_list = []
        for j in stock_folio:
            st_name = models.Stock.objects.filter(pk=j.sid_id)[0].ticker
            stock_list.append([j, st_name])
        data[i.pname] = stock_list
    form = forms.PortfolioForm()
    context = {'data': data, 'form': form}
    return render(request, 'client/portfolio.html', context)


def order_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('login')

    if request.method == 'POST':
        form = forms.OrderForm(data=request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            portfolio = form.cleaned_data['portfolio']
            broker = form.cleaned_data['broker']
            exchange = form.cleaned_data['exchange']
            order_type = form.cleaned_data['order_type']
            stock = form.cleaned_data['stock']
            price = form.cleaned_data['price']
            quantity = form.cleaned_data['quantity']
            client = models.Client.objects.filter(username=request.user.username).first()
            holding = models.Holdings.objects.filter(folio_id=portfolio, sid=stock).first()

            # check all objects are ok
            if any([t is None for t in [client, portfolio, stock, broker, exchange, holding]]) or order_type not in ('Buy', 'Sell'):
                messages.error(request, 'Invalid order.')

            cost = Decimal(quantity * price)
            commission = (broker.commission * cost) / 100

            # check if stock is listed at the exchange
            if not models.ListedAt.objects.filter(sid=stock, eid=exchange).exists():
                messages.error(request, 'Stock is not listed at this exchange.')
            # check if broker is registered at the exchange
            elif not models.RegisteredAt.objects.filter(bid=broker, eid=exchange).exists():
                messages.error(request, 'Broker is not registered at this exchange.')
            # in any order_type, check if commission balance is present
            # if order_type is buy, check if balance is enough
            elif order_type == 'Buy' and client.balance < commission + cost:
                messages.error(request, 'Insufficient balance.')
            # if order_type is sell, check if stock quantity in holdings >= specified holdings
            elif order_type == 'Sell' and (client.balance < commission or holding.quantity < quantity):
                if client.balance < commission:
                    messages.error(request, 'Insufficient balance.')
                if holding.quantity < quantity:
                    messages.error(request, 'Insufficient stocks.')
            else:
                # create the order
                neworder = models.BuySellOrder(folio_id=portfolio, bid=broker, eid=exchange, sid=stock, quantity=quantity, completed_quantity=0, price=price, creation_time=timezone.now(), order_type=order_type)
                # neworder = models.PendingOrder(folio_id=portfolio, bid=broker, eid=exchange, sid=stock, quantity=quantity, price=price, creation_time=timezone.now(), order_type=order_type)
                
                # give commission to broker
                broker.balance += commission
                # update the holdings and holding balance of client
                if order_type == 'Buy':
                    holding.quantity += quantity
                    holding.total_price += cost
                    client.balance -= commission + cost
                    client.holding_balance += cost
                # total_price in holdings can be negative ideally
                else:
                    holding.quantity -= quantity
                    holding.total_price -= cost
                    client.balance -= commission

                neworder.save()
                client.save()
                broker.save()
                holding.save()

                messages.success(request, 'Your order has been placed.')
                form = forms.OrderForm()
    else:
        form = forms.OrderForm()
    return render(request, 'client/placeorder.html', {'form': form})
