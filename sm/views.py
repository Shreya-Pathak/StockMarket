from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import sm.forms as allforms
import sm.models as allmodels
# Create your views here.
def index(request):
	return render(request, 'index.html', {})
    # return HttpResponse("You're at the stockmarket index.")
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
