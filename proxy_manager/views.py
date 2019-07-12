import MySQLdb
import random
import string
from django.shortcuts import render
from.proxy_manager import ProxyManager
from django.http import JsonResponse
from slacker import Slacker
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect


# Create your views here.
from django import forms
#menu 1,2,3,4


class Login:

    id_auth_pairs = list()

    @staticmethod
    def login(request):

        if request.method == "GET":

            return render(request, 'proxy_manager/login.html')

        if request.method == "POST":

            status = ProxyManager.instance().listen_status()

            user_id = request.POST['user_id']
            input_auth_number = request.POST['auth_number']

            for pair in Login.id_auth_pairs:

                if pair['user_id'] == user_id and pair['code'] == input_auth_number:

                    Login.id_auth_pairs.remove(pair)
                    request.session['login'] = True
                    return render(request, 'proxy_manager/main.html', {'listening_status': status})

            return render(request, 'proxy_manager/login.html')

    @staticmethod
    def auth_using_slack(request):
        #slack = Slacker('xoxp-188644484023-638488313699-681210631766-223c26295947f2bd6408b46759c9db61')
        user_id = request.POST['user_id']

        db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
        cur = db.cursor()
        query = "SELECT * FROM hamon_user WHERE user_id = '" + str(user_id) + "'"
        cur.execute(query)
        data = cur.fetchone()
        print(data)
        db.close()

        if data is not None:
            code = list()
            for i in range(5):
                char = random.choice(string.ascii_letters)
                code.append(char)

            code = "".join(code)

            new_pair = {'user_id': user_id, 'code': code}

            flag = 0
            for pair in Login.id_auth_pairs:
                if pair['user_id'] == user_id:
                    pair['code'] = code
                    flag = 1
                    break

            if flag == 0:
                Login.id_auth_pairs.append(new_pair)

            print(Login.id_auth_pairs)
            #slack.chat.post_message(data[1], code, "")

        data = {'message': '슬랙에서 코드를 확인하세요'}

        return JsonResponse(data)

        # get user info from slack and
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
        # return render(request, 'proxy_manager/login.html', {'form': form})


def node_proxy_close(request):

    node_proxy_key = request.POST['node_proxy_key']

    node_foward_info = {'node_proxy_key': node_proxy_key}

    ProxyManager.instance().close_command(node_foward_info)

    data = {'message': '실행하였다.'}

    return JsonResponse(data)


def node_proxy_forward(request):

    print("foward")
    node_proxy_key = request.POST['node_proxy_key']
    des_ip = request.POST['dest_ip']
    des_port = request.POST['dest_port']

    node_foward_info = {'node_proxy_key': node_proxy_key, 'des_ip': des_ip, 'des_port': des_port}

    print(node_foward_info)
    ProxyManager.instance().transfer_command(node_foward_info)

    data = {'message': '실행하였다.'}

    return JsonResponse(data)


def node_proxy_list(request):

    node_proxy_list = ProxyManager.instance().node_proxy_list

    for node in node_proxy_list:
        print(node)

    return render(request, 'proxy_manager/node_proxy_list.html', {'node_proxy_list': node_proxy_list})


def main(request):
    if request.session.get('login', False):

        status = ProxyManager.instance().listen_status()

        return render(request, 'proxy_manager/main.html', {'listening_status': status})
    else:
        return render(request, 'proxy_manager/login.html')


def static_apply_form(request):
    if request.session.get('login', False):

        return render(request, 'proxy_manager/static_apply_form.html')
    else:
        return render(request, 'proxy_manager/login.html')


def static_status(request):
    if request.session.get('login', False):
        static_proxy_info = ProxyManager.instance().get_static_status()
        context = {'form': static_proxy_info}

        return render(request, 'proxy_manager/static_status.html', context)
    else:
        return render(request, 'proxy_manager/login.html')


def static_apply_list(request):
    if request.session.get('login', False):
        static_proxy_info = ProxyManager.instance().get_static_apply_list()
        context = {'form': static_proxy_info}

        return render(request, 'proxy_manager/static_apply_list.html', context)
    else:
        return render(request, 'proxy_manager/login.html')


#ajax process


def timer_cancel(request):

    proxy_number = int(request.POST['proxy_number'])
    dynamic_proxy = ProxyManager.instance().get_proxy(proxy_number)

    dynamic_proxy.timer_use_yn = 'n'
    data = {'message': '성공했다.'}

    return JsonResponse(data)

def timer_on(request):

    proxy_number = int(request.POST['proxy_number'])
    dynamic_proxy = ProxyManager.instance().get_proxy(proxy_number)
    dynamic_proxy.listen_stop()

    dynamic_proxy.timer_use_yn = 'y'
    data = {'message': '성공했다.'}

    return JsonResponse(data)

def del_proxy(request):

    static_port = request.POST['static_port']

    ProxyManager.instance().del_static_proxy(static_port)

    data = {'message': '지워졌다.'}

    return JsonResponse(data)


def apply_ok(request):

    static_port = request.POST['static_port']
    des_ip = request.POST['des_ip']
    des_port = request.POST['des_port']
    user_name = request.POST['user_name']
    date_limit = request.POST['date_limit']

    ProxyManager.instance().add_static_proxy(static_port, des_ip, des_port, user_name, date_limit)

    data = {'message': '승인되었다'}

    return JsonResponse(data)


def static_apply_submit(request):

    static_port = request.POST['static_port']
    des_ip = request.POST['des_ip']
    des_port = request.POST['des_port']
    user_name = request.POST['user_name']
    date_limit = request.POST['date_limit']

    ProxyManager.instance().set_static_apply_submit(static_port, des_ip, des_port, user_name, date_limit)

    return render(request, 'proxy_manager/static_apply_form.html')


def proxy(request):

    proxy_number = int(request.POST['proxy_number'])
    dest_ip = request.POST['dest_ip']
    dest_port = request.POST['dest_port']

    proxy_manager = ProxyManager.instance()

    proxy = proxy_manager.get_proxy(proxy_number)
    proxy.set_des(dest_ip, dest_port)

    proxy.listen_start()

    data = {
        'message': "30초 안에 접속하세요"
    }

    return JsonResponse(data)


def apply_reject(request):

    port_number = request.POST['static_port']

    ProxyManager.instance().static_apply_reject(port_number)

    data = {"message": "신청을 거절했습니다."}

    return JsonResponse(data)


def admin_login(request):

    form = AuthenticationForm()
    form.fields['username'].widget.attrs['class'] = 'form-control'
    form.fields['username'].widget.attrs['placeholder'] = 'Admin ID'
    form.fields['password'].widget.attrs['class'] = 'form-control'
    form.fields['password'].widget.attrs['placeholder'] = 'Password'

    return render(request, 'proxy_manager/admin_login.html', {'form': form})


def admin_login_action(request):

    id = request.POST['username']
    password = request.POST['password']

    db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
    cur = db.cursor()
    query = "SELECT password FROM hamon_admin WHERE id = '" + str(id) + "'"
    cur.execute(query)
    db_password = cur.fetchone()

    print(db_password[0])
    print(password)
    if password == db_password[0]:
        request.session['login'] = True
        request.session['mode'] = 'admin'
        request.session.set_expiry(0)
        return redirect('main')
    else:
        return redirect('login')






