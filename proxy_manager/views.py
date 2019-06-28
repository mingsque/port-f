from django.shortcuts import render

from .forms import LoginForm
import MySQLdb

from django.http import HttpResponse

# Create your views here.
from django import forms


def proxy(request):

    dest_ip = request.POST['dest_ip']
    dest_port = request.POST['dest_port']

    print(dest_ip + "," + dest_port)




def index(request):

    form = LoginForm()

    return render(request, 'proxy_manager/login.html', {'form': form})


def main(request):

    db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")

    cur = db.cursor()

    cur.execute("SELECT * FROM django_content_type")

    for row in cur.fetchall():
        print(row[1])

    db.close()

    print("open main")
    id = request.POST.get('id')
    print(request.method)
    print(id)
    form = LoginForm(request.POST)

    return render(request, 'proxy_manager/main.html')
'''
    id = request.POST['id']
    password = request.POST['password']

    print("id : ".format(id))
    print("password : ".format(password))
'''
