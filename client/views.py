from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import client.forms as forms
import market.models as models
from django.contrib import messages

# Create your views here.


def check_user(request):
    if not request.user.is_authenticated:
        return False
    if not models.Client.objects.filter(email=request.user.email).exists():
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
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return HttpResponseRedirect('login')
            user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
            user.save()
            person = models.Person(name=name, address=address, telephone=telephone)
            person.save()
            client = models.Client(clid=person, email=email)
            client.save()
            messages.info(request, 'You can now login using your new account.')
            return HttpResponseRedirect('login')
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
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, 'Successfully logged in.')
                return HttpResponseRedirect('home')
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
        messages.error('Please login first.')
        return HttpResponseRedirect('login')

    all_folios = models.Portfolio.objects.filter(clid__email=request.user.email).order_by('pname')

    data = {}
    for i in all_folios:
        stock_folio = models.Holdings.objects.filter(folio_id_id=i.folio_id)
        stock_list = []
        for j in stock_folio:
            st_name = models.Stock.objects.filter(pk=j.sid_id)[0].ticker
            stock_list.append([j, st_name])
        data[i.pname] = stock_list
    context = {'data': data}
    return render(request, 'client/portfolio.html', context)