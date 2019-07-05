from django import forms
from django.contrib.auth.forms import AuthenticationForm





class StaticApplyForm(forms.Form):

    static_port = forms.IntegerField(help_text="input static port")
    des_ip = forms.CharField(help_text="input destination ip address")
    des_port = forms.IntegerField(help_text="input destination port number")
    user_name = forms.CharField(help_text="input user name")
    date_limit = forms.DateField(help_text="Input limit date")

