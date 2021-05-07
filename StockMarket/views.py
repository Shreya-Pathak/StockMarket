from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
import StockMarket.forms as forms
import market.models as models
from market.views import render
from django.contrib import messages
from time import sleep
from django.db import transaction
# Create your views here.


def home_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    obj = models.Client.objects.filter(username=request.user.username).first()
    if obj is not None:
        return HttpResponseRedirect('/client/home')
    obj = models.Broker.objects.filter(username=request.user.username).first()
    if obj is not None:
        return HttpResponseRedirect('/broker/home')
    return HttpResponseRedirect('/admin')


def index_view(request):
    return render(request, 'index.html', {})


def login_view(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already logged in.')
        return HttpResponseRedirect('home')
    client_form = forms.ClientLoginForm()
    broker_form = forms.BrokerLoginForm()
    if request.method == 'POST':
        if 'client_login' in request.POST:
            client_form = forms.ClientLoginForm(request.POST)
            if client_form.is_valid():
                username = client_form.cleaned_data.get('username')
                password = client_form.cleaned_data.get('password')
                if models.Client.objects.filter(username=username).first() is None:
                    messages.warning(request, 'You can\'t login as a client.')
                else:
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        messages.info(request, 'Successfully logged in.')
                        return HttpResponseRedirect('client/home')
                    messages.error(request, 'Wrong username/password.')
        if 'broker_login' in request.POST:
            broker_form = forms.BrokerLoginForm(request.POST)
            if broker_form.is_valid():
                username = broker_form.cleaned_data.get('username')
                password = broker_form.cleaned_data.get('password')
                if models.Broker.objects.filter(username=username).first() is None:
                    messages.warning(request, 'You can\'t login as a broker.')
                else:
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        messages.info(request, 'Successfully logged in.')
                        return HttpResponseRedirect('broker/home')
                    messages.error(request, 'Wrong username/password.')
    return render(request, 'login.html', {'client_form': client_form, 'broker_form': broker_form})


def signup_view(request):
    if request.user.is_authenticated:
        messages.error(request, 'You are already logged in.')
        return HttpResponseRedirect('home')
    client_form = forms.ClientSignUpForm()
    broker_form = forms.BrokerSignUpForm()
    if request.method == 'POST':
        if 'client_signup' in request.POST:
            # print(request.POST)
            client_form = forms.ClientSignUpForm(request.POST)
            if client_form.is_valid():
                name = client_form.cleaned_data.get('name')
                email = client_form.cleaned_data.get('email')
                address = client_form.cleaned_data.get('address')
                telephone = client_form.cleaned_data.get('telephone')
                password = client_form.cleaned_data.get('password')
                username = email.split('@')[0]
                if not User.objects.filter(username=username).exists():
                    
                    try:
                        with transaction.atomic():
                            user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
                            user.save()
                            person = models.Person(name=name, address=address, telephone=telephone)
                            person.save()
                            client = models.Client(clid=person, username=username, balance=0)
                            client.save()
                        messages.info(request, 'You can now login using your new client account.')
                        return HttpResponseRedirect('login')
                    except :
                        messages.error(request, 'Username already exists')
                        return render(request, 'signup.html', {'client_form': client_form, 'broker_form': broker_form})
                messages.error(request, "Username already exists.")
        if 'broker_signup' in request.POST:
            broker_form = forms.BrokerSignUpForm(request.POST)
            if broker_form.is_valid():
                name = broker_form.cleaned_data.get('name')
                email = broker_form.cleaned_data.get('email')
                address = broker_form.cleaned_data.get('address')
                telephone = broker_form.cleaned_data.get('telephone')
                password = broker_form.cleaned_data.get('password')
                commission = broker_form.cleaned_data.get('commission')
                username = email.split('@')[0]
                if not User.objects.filter(username=username).exists():
                    
                    try:
                        with transaction.atomic():
                            user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
                            user.save()
                            person = models.Person(name=name, address=address, telephone=telephone)
                            person.save()
                            broker = models.Broker(bid=person, username=username, balance=0, orders_approved=0, latency=0, commission=commission)
                            broker.save()
                        messages.info(request, 'You can now login using your new broker account.')
                        return HttpResponseRedirect('login')
                    except :
                        messages.error(request, 'Username already exists')
                        return render(request, 'signup.html', {'client_form': client_form, 'broker_form': broker_form})
                messages.add_message(request, messages.ERROR, "Username already exists.")
    return render(request, 'signup.html', {'client_form': client_form, 'broker_form': broker_form})