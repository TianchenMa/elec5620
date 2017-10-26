import time

from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput, required=True)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput, required=True)
    password_confirm = forms.CharField(max_length=32, widget=forms.PasswordInput, required=True)
    register_code = forms.CharField(max_length=100, required=True)


class HealthDataForm(forms.Form):
    heart_rate = forms.IntegerField(required=True)
    weight = forms.FloatField(max_value=500, min_value=0)
    temperature = forms.FloatField(max_value=200, min_value=0)


class ActivityForm(forms.Form):
    title = forms.CharField(max_length=100, required=True)
    content = forms.CharField(max_length=300, required=False)
