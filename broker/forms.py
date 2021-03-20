from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset, Div

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
decimals = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')


class SignUpForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Required'}))
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    commission = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}), validators=[decimals])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout('email', 'password', 'name', 'address', 'telephone', 'commission', Submit('submit', 'Sign Up', css_class='btn btn-primary'))


class LoginForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Required'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout('username', 'password', Submit('submit', 'Login', css_class='btn btn-primary'))


FRUIT_CHOICES = [('None','None'),('price', 'Price'), ('creation_time','Date'), ('quantity', 'Quantity')]
TYPE_CHOICES=[('All', 'All'), ('Buy', 'Buy'), ('Sell', 'Sell')]

class SorterForm(forms.Form):
    sortfield = forms.CharField(label='Sort by', widget=forms.Select(choices=FRUIT_CHOICES), required=False)
    order_type = forms.CharField(label='Order type', widget=forms.Select(choices=TYPE_CHOICES), required=False)
    ticker = forms.CharField(label='Ticker', max_length=30, required=False)
    exchange = forms.CharField(label='Exchange', max_length=30, required=False)
    client = forms.CharField(label='Exchange', max_length=30, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'form-group form-inline'
        self.fields['sortfield'].label='Sort by'
        self.fields['order_type'].label='Type'
        self.fields['ticker'].label='Ticker'
        self.fields['exchange'].label='Exchange'
        self.fields['client'].label='Client'
        # self.helper.field_class = 'col-sm-4'
        self.helper.layout = Layout(Div(Div('ticker',css_class='col-lg-4'),Div('exchange',css_class='col-lg-4'),Div('client',css_class='col-lg-4'),css_class='row w-50 container justify-content-center'),
                    Div(Div('sortfield',css_class='col-lg-2'),Div('order_type',css_class='col-lg-2'),css_class='row w-20 container justify-content-center with-margin'),
                    Submit('submit', 'Filter', css_class=' justify-content-center  '))
            # 'client',css_class='row')
            # Div('sortfield','order_type',css_class='with-margin'), Submit('submit', 'Add Portfolio', css_class='btn btn-primary'))
