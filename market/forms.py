from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset, Div

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
decimals = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')

STOCK_SORT_CHOICES = [('Ticker', 'Ticker'), ('Exchange', 'Exchange'), ('Latest Price', 'Latest Price'), ('Change', 'Change')]
class StockSorterForm(forms.Form):
    sortfield = forms.CharField(label='Sort by', widget=forms.Select(choices=STOCK_SORT_CHOICES), required=False)
    ticker = forms.CharField(label='Ticker', max_length=30, required=False)
    exchange = forms.CharField(label='Exchange', max_length=30, required=False)


COMPANY_SORT_CHOICES = [('Ticker', 'Ticker'), ('Name', 'Name'), ('Country', 'Country')]
class CompanySorterForm(forms.Form):
    sortfield = forms.CharField(label='Sort by', widget=forms.Select(choices=COMPANY_SORT_CHOICES), required=False)
    name = forms.CharField(label='Name', max_length=100, required=False)
    country = forms.CharField(label='Country', max_length=30, required=False)
    sector = forms.CharField(label='Sector', max_length=30, required=False)


class AddAcctForm(forms.Form):
    acct_no = forms.IntegerField(label='Account Number', required=True, widget=forms.NumberInput(attrs={'placeholder': 'Required'}))
    name = forms.CharField(label='Bank Name', max_length=100, required=True)
    balance = forms.IntegerField(label='Balance', required=True, widget=forms.NumberInput(attrs={'placeholder': 'Required'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(Div('acct_no', css_class='with-margin'), Div('name', css_class='with-margin'), Div('balance', css_class='with-margin'), Submit('submit', 'Add Account', css_class='btn btn-primary'))
