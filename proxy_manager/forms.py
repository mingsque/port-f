from django import forms


class LoginForm(forms.Form):
    id = forms.CharField(label='id', max_length=30)
    password = forms.CharField(label='password')


class StaticApplyForm(forms.Form):

    static_port = forms.IntegerField(help_text="input static port")
    des_ip = forms.CharField(help_text="input destination ip address")
    des_port = forms.IntegerField(help_text="input destination port number")
    user_name = forms.CharField(help_text="input user name")
    date_limit = forms.DateField(help_text="Input limit date")
