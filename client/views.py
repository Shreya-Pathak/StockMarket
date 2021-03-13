from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
import client.forms as forms
import market.models as models

# Create your views here.


def index_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    else:
        return HttpResponseRedirect('login')


def signup_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    if request.method == 'POST':
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            person = models.Person(name=form.cleaned_data.get('name'), address=form.cleaned_data.get('address'), telephone=form.cleaned_data.get('telephone'))
            person.save()
            client = models.Client(bid=person, email=email)
            client.save()
            user = User.objects.create_user(username=email.split('@')[0], password=form.cleaned_data.get('password'))
            user.save()
            return HttpResponseRedirect('login')
    else:
        form = forms.SignUpForm()
    return render(request, 'client/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('home')
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('home')
    else:
        form = forms.LoginForm()
    return render(request, 'client/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return HttpResponseRedirect('login')


def home_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('login')
    return render(request, 'client/home.html')
