from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset, Div
from . import models
from django.forms import ModelChoiceField
from bootstrap_datepicker_plus import DatePickerInput

from dal import autocomplete, forward

class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.ticker

class MyModelChoiceField1(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.name

class MyModelChoiceField_ind(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.index_name

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

# class corrForm(forms.ModelForm):
#     birth_country = forms.ModelChoiceField(
#         queryset=models.Stock.objects.all(),
#         widget=autocomplete.ModelSelect2(url='stock-autocomplete')
#     )

#     class Meta:
#         model = models.Stock
#         fields = ('__all__')


class corrForm(forms.Form):
    corrs = ModelChoiceField(label='Stock', queryset=models.Stock.objects.all())
    corre = MyModelChoiceField1(label='Exchange', queryset=models.Exchange.objects.all().order_by('name'))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = kwargs.pop('data', None)
        if data is not None:
            self.fields['corre'].queryset = models.Stock.objects.filter(pk=int(data['stock']))

class OrderForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=models.Stock.objects.all(), widget=autocomplete.ModelSelect2(url='stock-autocomplete', attrs={'data-placeholder': 'Search'}))
    exchange = forms.ModelChoiceField(queryset=models.Exchange.objects.none(), widget=autocomplete.ModelSelect2(url='exchange-autocomplete', attrs={'data-placeholder': 'Search'}, forward=['stock']))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-6 mb-0'
        self.helper.layout = Layout(Div('stock', css_class='with-margin'), Div('exchange', css_class='with-margin'), Submit('submit', 'Calculate Correlation', css_class='btn btn-primary'))
        data = kwargs.pop('data', None)
        if data is not None:
            self.fields['stock'].queryset = models.Stock.objects.filter(pk=int(data['stock']))
            self.fields['exchange'].queryset = models.Exchange.objects.filter(pk=int(data['exchange']))
            
class corrForm_ind(forms.Form):
    # corrs = MyModelChoiceField_ind(label='Index', queryset=models.Indices.objects.all().order_by('index_name'))
    index = forms.ModelChoiceField(queryset=models.Indices.objects.all(), widget=autocomplete.ModelSelect2(url='index-autocomplete', attrs={'data-placeholder': 'Search'}),  to_field_name="index_name")
    # corre = MyModelChoiceField1(label='Exchange', queryset=models.Exchange.objects.all().order_by('name'))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-6 mb-0'
        self.helper.layout = Layout(Div('index', css_class='with-margin'), Submit('submit', 'Calculate Correlation', css_class='btn btn-primary'))
        data = kwargs.pop('data', None)
        if data is not None:
            self.fields['index'].queryset = models.Indices.objects.filter(pk=int(data['index']))

class dateForm(forms.Form):
     start = forms.CharField(label='From'
        
    )
     end = forms.CharField(label='To'
        
    )
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper()
    #     self.helper.form_class = 'form-horizontal'
    #     self.helper.label_class = 'col-lg-4'
    #     self.helper.field_class = 'col-lg-8'
    #     self.helper.layout = Layout(Div('acct_no', css_class='with-margin'), Div('name', css_class='with-margin'), Div('balance', css_class='with-margin'), Submit('submit', 'SetDate', css_class='btn btn-primary'))