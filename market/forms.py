from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
decimals = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')

FRUIT_CHOICES = [('Ticker', 'Ticker'), ('Exchange', 'Exchange'), ('Latest Price', 'Latest Price')]

class SorterForm(forms.Form):
    sortfield = forms.CharField(label='Sort by', widget=forms.Select(choices=FRUIT_CHOICES), required=False)
    ticker = forms.CharField(label='Ticker', max_length=30, required=False)
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
