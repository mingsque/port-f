from django.shortcuts import render

from .forms import LoginForm
import MySQLdb
from .proxy import Proxy
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.http import JsonResponse

# Create your views here.
from django import forms


def proxy(request):

    print(request.POST)
    dest_ip = request.POST['dest_ip']
    dest_port = request.POST['dest_port']

    proxy = Proxy(10500, dest_ip, dest_port)
    proxy.listen_start()

    print(dest_ip + "," + dest_port)

    data = {
        'dest_ip': dest_ip,
        'dest_port': dest_port
    }

    return JsonResponse(data)

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
