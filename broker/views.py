from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
import broker.forms as forms
import market.models as models
from django.contrib import messages
from django.utils import timezone

# Create your views here.


def check_user(request):
    if not request.user.is_authenticated:
        return False
    broker = models.Broker.objects.filter(username=request.user.username).first()
    if broker is None:
        messages.warning(request, 'You do not have access to this page.')
        return True
    return False


def index_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    else:
        return HttpResponseRedirect('/login')


def logout_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Successfully logged out.')
    return HttpResponseRedirect('/login')


def home_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')
    return render(request, 'broker/home.html')


def past_order_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('/login')
    brid = models.Broker.objects.filter(username=request.user.username).first()
    assert brid is not None
    oldorder = models.OldOrder.objects.select_related('sid', 'eid', 'folio_id__clid__clid').filter(bid=brid)
    currorder = models.BuySellOrder.objects.select_related('sid', 'eid', 'folio_id__clid__clid').filter(bid=brid)
    formog = forms.SorterForm()

    if request.method == 'POST':
        form = forms.SorterForm(request.POST)
        if form.is_valid():
            sortfield = form.cleaned_data.get('sortfield')
            order_type = form.cleaned_data.get('order_type')
            ticker = form.cleaned_data.get('ticker')
            exchange = form.cleaned_data.get('exchange')
            client = form.cleaned_data.get('client')
            if order_type != 'All':
                oldorder = oldorder.filter(order_type=order_type)
                currorder = currorder.filter(order_type=order_type)
                formog.fields['order_type'].initial = order_type
            if sortfield != 'None':
                oldorder = oldorder.order_by(sortfield)
                currorder = currorder.order_by(sortfield)
                formog.fields['sortfield'].initial = sortfield
            if ticker != '':
                oldorder = oldorder.filter(sid__ticker__icontains=ticker)
                currorder = currorder.filter(sid__ticker__icontains=ticker)
            if exchange != '':
                oldorder = oldorder.filter(eid__name__icontains=exchange)
                currorder = currorder.filter(eid__name__icontains=exchange)
            if client != '':
                oldorder = oldorder.filter(folio_id__clid__clid__name__icontains=client)
                currorder = currorder.filter(folio_id__clid__clid__name__icontains=client)

    oldorder = oldorder.all()
    currorder = currorder.all()

    context = {'oldorders': oldorder, 'currorder': currorder, 'form': formog}
    return render(request, 'broker/past_orders.html', context)


def approve_order_view(request):
    if request.method == 'POST':
        order_id = get_from_request(request.POST)
        broker = models.Broker.objects.filter(username=request.user.username).first()
        order = models.PendingOrder.objects.select_related('bid').filter(pk=order_id).first()
        if order.bid.bid != broker.bid:
            messages.error(request, '')
            return HttpResponseRedirect('approve_order')
        neworder = models.BuySellOrder(folio_id=order.folio_id, bid=order.bid, eid=order.eid, sid=order.sid, quantity=order.quantity, completed_quantity=0, price=order.price, creation_time=order.creation_time, order_type=order.order_type)
        delay = (timezone.now() - order.creation_time).total_seconds()
        n = broker.orders_approved
        broker.latency += (delay - broker.latency) // (n + 1)
        broker.orders_approved += 1
        order.delete()
        neworder.save()
        broker.save()

    # display orders from pending orders table
    pass


def withdraw_view(request):
    return render(request, 'broker/withdraw.html', {})


def add_funds_view(request):
    return render(request, 'broker/add_funds.html', {})


def companies_view(request):
    return render(request, 'broker/companies.html', {})