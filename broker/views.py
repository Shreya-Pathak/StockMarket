from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
import broker.forms as forms
import market.models as models
from django.contrib import messages

# Create your views here.


def check_user(request):
    if not request.user.is_authenticated:
        return False
    if not models.Broker.objects.filter(email=request.user.email).exists():
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
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return HttpResponseRedirect('login')
            user = User.objects.create_user(username=username, email=email, password=password, first_name=name)
            user.save()
            person = models.Person(name=name, address=address, telephone=telephone)
            person.save()
            broker = models.Broker(bid=person, email=email, commission=commission)
            broker.save()
            messages.info(request, 'You can now login using your new account.')
            return HttpResponseRedirect('login')
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
