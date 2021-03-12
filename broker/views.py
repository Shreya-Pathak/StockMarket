from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import broker.forms as forms
import market.models as allmodels

# Create your views here.


def index(request):
    return HttpResponseRedirect('/signup')


def signup(request):
    if request.method == 'POST':
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            user = allmodels.Person(name=form.cleaned_data.get('name'), address=form.cleaned_data.get('address'), telephone=form.cleaned_data.get('telephone'))
            # user.refresh_from_db()  # load the profile instance created by the signal
            user.save()
            # print(user.id,end='****\n')
            broker = allmodels.Broker(id=user, commission=form.cleaned_data.get('commission'), latency=form.cleaned_data.get('latency'))
            broker.save()
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=user.username, password=raw_password)
            # login(request, user)
            # return redirect('home')
            return HttpResponseRedirect('/signup/')
    else:
        form = forms.SignUpForm()
    return render(request, 'broker_signup.html', {'form': form})
