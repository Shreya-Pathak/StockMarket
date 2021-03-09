

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')

class SignUpForm(forms.Form):
    # birth_date = forms.DateField(help_text='Required. Format: YYYY-MM-DD')
    name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    address= forms.CharField(max_length=30, required=False, help_text='Optional.')
    telephone = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.CharField(max_length=30, required=False, help_text='Optional.')
    account_number = forms.CharField(max_length=30, required=False, help_text='Optional.',validators=[numeric])
    # class Meta:
    #     model = User
    #     fields = ('username', 'birth_date', 'password1', 'password2', )
    # def clean(self):
 
    #     # data from the form is fetched using super function
    #     super(SignUpForm, self).clean()
         
    #     # extract the username and text field from the data
    #     username = self.cleaned_data.get('username')
    #     ac = self.cleaned_data.get('account_number')

    #     # conditions to be met for the username length
    #     if ac.isdigit():
    #         self._errors['username'] = self.error_class([
    #             'ac must have digits only'])
    #     # if len(text) <10:
    #     #     self._errors['text'] = self.error_class([
    #     #         'Post Should Contain a minimum of 10 characters'])

    #     # return any errors if found
    #     return self.cleaned_data