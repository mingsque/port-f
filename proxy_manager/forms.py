from django import forms


class LoginForm(forms.Form):
    id = forms.CharField(label='id', max_length=30)
    password = forms.CharField(label='password')