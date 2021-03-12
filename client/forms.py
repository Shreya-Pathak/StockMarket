from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Reset, Fieldset

numeric = RegexValidator(r'^[0-9]+$', 'Only digit characters.')
decimals = RegexValidator(r'^\d+[.,]?\d*$|^\d*[.,]?\d+$', 'Only decimal numbers.')

class SignUpForm(forms.Form):
    name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    address = forms.CharField(max_length=30, required=False, help_text='Optional.')
    telephone = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.CharField(max_length=30, required=False, help_text='Optional.')
    account_number = forms.CharField(max_length=30, required=False, help_text='Optional.', validators=[numeric])