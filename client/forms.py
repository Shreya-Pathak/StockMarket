from dal import autocomplete
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset, Div
import market.models as models

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
decimals = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')


class SignUpForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Required'}))
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))
    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout('email', 'password', 'name', 'address', 'telephone', Submit('submit', 'Sign Up', css_class='btn btn-primary'))


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


class PortfolioForm(forms.Form):
    pname = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Required'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.fields['pname'].label = 'Portfolio Name'
        self.helper.field_class = 'col-lg-6'
        self.helper.layout = Layout(Div('pname', css_class='with-margin'), Submit('submit', 'Add Portfolio', css_class='btn btn-primary'))


class OrderForm(forms.Form):
    order_type = forms.ChoiceField(required=True, choices=[('Buy', 'Buy'), ('Sell', 'Sell')], widget=forms.RadioSelect)
    quantity = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'placeholder': 'Required'}))
    portfolio = forms.ModelChoiceField(queryset=models.Portfolio.objects.none(), widget=autocomplete.ModelSelect2(url='portfolio-autocomplete', attrs={'data-placeholder': 'Search'}))
    stock = forms.ModelChoiceField(queryset=models.Stock.objects.none(), widget=autocomplete.ModelSelect2(url='stock-autocomplete', attrs={'data-placeholder': 'Search'}, forward=['order_type', 'portfolio', 'quantity']))
    exchange = forms.ModelChoiceField(queryset=models.Exchange.objects.none(), widget=autocomplete.ModelSelect2(url='exchange-autocomplete', attrs={'data-placeholder': 'Search'}, forward=['stock']))
    broker = forms.ModelChoiceField(queryset=models.Broker.objects.none(), widget=autocomplete.ModelSelect2(url='broker-autocomplete', attrs={'data-placeholder': 'Search'}, forward=['exchange']))
    price = forms.FloatField(required=True, widget=forms.NumberInput(attrs={'placeholder': 'Required'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-6'
        self.helper.layout = Layout(
            Div('order_type', css_class='with-margin'), 
            Div('quantity', css_class='with-margin'), 
            Div('portfolio', css_class='with-margin'), 
            Div('stock', css_class='with-margin'), 
            Div('exchange', css_class='with-margin'), 
            Div('broker', css_class='with-margin'), 
            Div('price', css_class='with-margin'), 
            Submit('submit', 'Place Order', css_class='btn btn-primary')
        )
        data = kwargs.pop('data', None)
        if data is not None:
            self.fields['portfolio'].queryset = models.Portfolio.objects.filter(pk=int(data['portfolio']))
            self.fields['stock'].queryset = models.Stock.objects.filter(pk=int(data['stock']))
            self.fields['exchange'].queryset = models.Exchange.objects.filter(pk=int(data['exchange']))
            self.fields['broker'].queryset = models.Broker.objects.filter(pk=int(data['broker']))