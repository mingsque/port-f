from django.shortcuts import render

from .forms import LoginForm
import MySQLdb
from .proxy import Proxy
from django.http import JsonResponse
from slacker import Slacker
import random
import string
from.proxy_manager import ProxyManager
import threading

# Create your views here.
from django import forms




def static_apply(request):

    return render(request, 'proxy_manager/main.html')


def proxy(request):

    proxy_manager = ProxyManager.instance()

    proxy_number = int(request.POST['proxy_number'])
    dest_ip = request.POST['dest_ip']
    dest_port = request.POST['dest_port']

    proxy = proxy_manager.get_proxy(proxy_number)
    proxy.set_dest(dest_ip, dest_port)
    proxy.listen_start()

    threading.Timer(10.0, proxy.listen_stop).start()

    data = {
        'message': "30초 안에 접속하세요"
    }

    return JsonResponse(data)


def login(request):

    return render(request, 'proxy_manager/login.html')


def login_action(request):
    manager = ProxyManager.instance()
    status = manager.listen_status()
    listening_status = dict()

    for i in range(5):
        listening_status[str(i)] = status[i]


    print(listening_status)
    id = request.POST['user_id']
    input_auth_number = request.POST['auth_number']

    #print("원래코드 : {}".format(code))
    #print("입력코드 : {}".format(input_auth_number))

    '''
    if input_auth_number == code:
        return render(request, 'proxy_manager/main.html')
    else:
        return render(request, 'proxy_manager/login.html')
    '''
    return render(request, 'proxy_manager/main.html', {'listening_status': status})


def auth_using_slack(request):
    slack = Slacker('xoxp-188644484023-638488313699-681210631766-223c26295947f2bd6408b46759c9db61')

    user_id = request.POST['user_id']
    print(user_id)

    db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
    cur = db.cursor()
    query = "SELECT * FROM hamon_user WHERE user_id = '" + str(user_id) + "'"
    print(query)
    cur.execute(query)
    data = cur.fetchone()

    print(data)
    db.close()

    global code
    code = list()

    for i in range(5):
        char = random.choice(string.ascii_letters)
        code.append(char)

    code = "".join(code)


    print(code)

    slack.chat.post_message(data[1], code, "")

    data = {'message': '슬랙에서 코드를 확인하세요'}

    return JsonResponse(data)

    #get user info from slack and
    '''
    response = slack.users.list()

    members = (response.body['members'])

    login_set = []
    
    for member in members:
        try:
            login_set.append((member['profile']['email'], member['id']))
        except:
            pass
    print(login_set)

    db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
    cur = db.cursor()
    query = "INSERT INTO hamon_user (user_id, slack_id) VALUES (%s,%s)"
    cur.executemany(query, login_set)
    db.commit()
    db.close()
    '''
    #return render(request, 'proxy_manager/login.html', {'form': form})


def main(request):

    print("open main")
    id = request.POST.get('id')
    print(request.method)
    print(id)
    form = LoginForm(request.POST)

    return render(request, 'proxy_manager/main.html')

