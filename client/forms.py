from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset

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
        self.helper.layout = Layout('email', 'password','name','address','telephone', Submit('submit', 'Sign Up', css_class='btn btn-primary'))


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
        self.helper.label_class = 'col-lg-6'
        self.fields['pname'].label='Portfolio Name'
        self.helper.field_class = 'col-lg-6'
        self.helper.layout = Layout('pname', Submit('submit', 'Add Portfolio', css_class='btn btn-primary'))
