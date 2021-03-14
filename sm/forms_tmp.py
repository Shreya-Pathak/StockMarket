

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
dec = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')

FRUIT_CHOICES=[('Ticker','Ticker'),('Exchange','Exchange'),('Latest Price','Latest Price')]

class SorterForm(forms.Form):
  sortfield= forms.CharField(label='Sort by', widget=forms.Select(choices=FRUIT_CHOICES),required=False)
  ticker=forms.CharField(label='Ticker', max_length=30, required=False)
  exchange = forms.CharField(label='Exchange', max_length=30, required=False)
  # def __init__(self, *args, **kwargs):
  #       super().__init__(*args, **kwargs)
  #       self.helper = FormHelper()
  #       self.helper.layout = Layout(
  #           Row(
  #               Column('ticker', css_class='form-group col-md-6 mb-0'),
  #               Column('exchange', css_class='form-group col-md-6 mb-0'),
  #               css_class='form-row'
  #           ),
  #           Submit('sfilt', 'Sort')
  #       )

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

class SignUpForm_Broker(forms.Form):
    # birth_date = forms.DateField(help_text='Required. Format: YYYY-MM-DD')
    name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    address= forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    telephone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    commission = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}), validators=[dec])
    latency = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}),validators=[dec])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        # self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name','address','telephone','commission', 'latency',
            Submit('submit', 'Sign Up', css_class='btn btn-primary')
        )