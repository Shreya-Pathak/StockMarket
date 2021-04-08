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


def check_user(request):
    if not request.user.is_authenticated:
        return False
    client = models.Client.objects.filter(username=request.user.username).first()
    if client is None:
        messages.warning(request, 'You do not have access to this page.')
        return True
    return False


def index_view(request):
    if check_user(request):
        return HttpResponseRedirect('/home')
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    else:
        return HttpResponseRedirect('/login')


def logout_view(request):
    if check_user(request):
        return HttpResponseRedirect('/home')
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Successfully logged out.')
    return HttpResponseRedirect('/login')


def home_view(request):
    if check_user(request):
        return HttpResponseRedirect('/home')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')
    return render(request, 'client/home.html')


def portfolio_view(request):
    if check_user(request):
        return HttpResponseRedirect('/home')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')
    client = models.Client.objects.filter(username=request.user.username).first()
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
        return HttpResponseRedirect('/home')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')

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
            # add stock to portfolio if doesnt exist
            if holding is None:
                holding = models.Holdings(folio_id=portfolio, sid=stock, quantity=0, total_price=0)

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
                    client.balance -= commission + cost
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


def cancel_order_view(request):
    if check_user(request):
        return HttpResponseRedirect('/home')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')
    if request.method == 'POST':
        order_id = get_from_request(request.POST)
        for model in [models.BuySellOrder, models.PendingOrder]:
            client = models.Client.objects.filter(username=request.user.username).first()
            order = model.objects.select_related('folio_id__clid').filter(pk=order_id).first()
            if order is None: continue
            rem_quantity = order.quantity - order.completed_quantity
            if order.folio_id.clid.clid != client.clid:
                messages.error(request, '')
                return HttpResponseRedirect('cancel_order')
            if order.order_type == 'Buy':
                client.balance += order.price * rem_quantity
                client.save()
            else:
                holding = models.Holdings.objects.filter(folio_id=order.folio_id, sid=order.sid).first()
                if holding is None:
                    messages.error(request, '')
                    return HttpResponseRedirect('cancel_order')
                holding.quantity += rem_quantity
                holding.total_price += rem_quantity * order.price
                holding.save()
            order.delete()
    # display pending orders
    pass