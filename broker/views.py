from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth.models import User
import broker.forms as forms
import market.models as models
from django.contrib import messages
from django.utils import timezone

# Create your views here.


def get_broker(username):
    broker = None
    try:
        broker = models.Broker.objects.get(username=username)
    except Exception as e:
        pass
    return broker


def check_user(request):
    if not request.user.is_authenticated:
        return False
    if get_broker(request.user.username) is None:
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
            commission = form.cleaned_data.get('commission')
            username = email.split('@')[0]
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
                user.save()
                person = models.Person(name=name, address=address, telephone=telephone)
                person.save()
                broker = models.Broker(bid=person, username=username, balance=0, commission=commission)
                broker.save()
                messages.info(request, 'You can now login using your new account.')
                return HttpResponseRedirect('login')
            messages.error(request, "Username already exists.")
    else:
        form = forms.SignUpForm()
    return render(request, 'broker/signup.html', {'form': form})


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
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, 'Successfully logged in.')
                return HttpResponseRedirect('home')
            if get_broker(username) is None:
                messages.warning(request, 'You can\'t login as a broker.')
            else:
                messages.error(request, 'Wrong username/password.')
    else:
        form = forms.LoginForm()
    return render(request, 'broker/login.html', {'form': form})


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
    return render(request, 'broker/home.html')


def order_view(request):
    if check_user(request):
        return HttpResponseRedirect('/')
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first.')
        return HttpResponseRedirect('login')
    brid = get_broker(request.user.username)
    assert brid is not None
    oldorder = models.OldOrder.objects.filter(bid=brid)
    currorder = models.BuySellOrder.objects.filter(bid=brid)
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
                # chosenlabel = dict(formog.fields['sortfield'].widget.choices)[sortfield]
                # ch = formog.fields['sortfield'].widget.choices
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
    return render(request, 'broker/myorders.html', context)
