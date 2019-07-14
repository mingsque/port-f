import MySQLdb
import random
import string
from django.shortcuts import render
from.proxy_manager import ProxyManager
from django.http import JsonResponse
from slacker import Slacker
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect

db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")


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

    @staticmethod
    def admin_login(request):

        if request.method == "GET":
            form = AuthenticationForm()
            form.fields['username'].widget.attrs['class'] = 'form-control'
            form.fields['username'].widget.attrs['placeholder'] = 'Admin ID'
            form.fields['password'].widget.attrs['class'] = 'form-control'
            form.fields['password'].widget.attrs['placeholder'] = 'Password'

            return render(request, 'proxy_manager/admin_login.html', {'form': form})

        if request.method == "POST":
            id = request.POST['username']
            password = request.POST['password']

            db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
            cur = db.cursor()
            query = "SELECT password FROM hamon_admin WHERE id = '" + str(id) + "'"
            cur.execute(query)
            db_password = cur.fetchone()

            if db_password is not None:
                if password == db_password[0]:
                    request.session['login'] = True
                    request.session['mode'] = 'admin'
                    request.session.set_expiry(0)
                    return redirect('main')
                else:
                    return redirect('login')
            else:
                return redirect('login')


def node_proxy_close(request):

    node_proxy_key = request.POST['node_proxy_key']

    node_foward_info = {'node_proxy_key': node_proxy_key}

    ProxyManager.instance().close_command(node_foward_info)

    data = {'message': '접속을 끊었습니다.'}

    return JsonResponse(data)


def node_proxy_forward(request):

    node_proxy_key = request.POST['node_proxy_key']
    des_ip = request.POST['dest_ip']
    des_port = request.POST['dest_port']

    node_foward_info = {'node_proxy_key': node_proxy_key, 'des_ip': des_ip, 'des_port': des_port}

    print(node_foward_info)
    ProxyManager.instance().transfer_command(node_foward_info)

    data = {'message': '목적지를 설정하였습니다.'}

    return JsonResponse(data)


def node_proxy_list(request):
    if request.session.get('login', False):

        node_proxy_list = ProxyManager.instance().node_proxy_list

        for node in node_proxy_list:
            print(node)

        return render(request, 'proxy_manager/node_proxy_list.html', {'node_proxy_list': node_proxy_list})
    else:
        return render(request, 'proxy_manager/login.html')


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

        cur = db.cursor()

        query = """SELECT   static_port_forwarding_info.static_port, 
                                       static_port_forwarding_info.des_ip, 
                                       static_port_forwarding_info.des_port, 
                                       static_port_forwarding_info.user_name, 
                                       static_port_forwarding_info.date_limit,
                                       data_use_amount.in_data,
                                       data_use_amount.out_data,
                                       data_use_amount.create_time,
                                       data_use_amount.update_time
                               FROM static_port_forwarding_info LEFT JOIN data_use_amount 
                               ON static_port_forwarding_info.static_port = data_use_amount.static_port
                            """
        cur.execute(query)
        static_proxy_info = cur.fetchall()

        cur.close()
        db.commit()

        context = {'form': static_proxy_info}

        return render(request, 'proxy_manager/static_status.html', context)
    else:
        return render(request, 'proxy_manager/login.html')


def static_apply_list(request):
    if request.session.get('login', False):

        cur = db.cursor()

        query = "SELECT * FROM static_port_forwarding_apply"
        cur.execute(query)

        static_proxy_info = cur.fetchall()

        cur.close()

        context = {'form': static_proxy_info}

        return render(request, 'proxy_manager/static_apply_list.html', context)
    else:
        return render(request, 'proxy_manager/login.html')


#ajax process
def timer_cancel(request):

    proxy_number = int(request.POST['proxy_number'])
    dynamic_proxy = ProxyManager.instance().get_proxy(proxy_number)

    dynamic_proxy.timer_use_yn = 'n'
    data = {'message': '고정하였습니다.'}

    return JsonResponse(data)


def timer_on(request):

    proxy_number = int(request.POST['proxy_number'])
    dynamic_proxy = ProxyManager.instance().get_proxy(proxy_number)
    dynamic_proxy.listen_stop()

    dynamic_proxy.timer_use_yn = 'y'
    data = {'message': '고정을 해제 하였습니다..'}

    return JsonResponse(data)


def del_proxy(request):

    static_port = request.POST['static_port']

    cur = db.cursor()
    query = "DELETE FROM static_port_forwarding_info WHERE static_port = " + str(static_port)
    cur.execute(query)
    db.commit()
    cur.close

    ProxyManager.instance().del_static_proxy(static_port)

    data = {'message': '고정포트를 지웠습니다.'}

    return JsonResponse(data)


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


def static_apply_submit(request):

    static_port = request.POST['static_port']
    des_ip = request.POST['des_ip']
    des_port = request.POST['des_port']
    user_name = request.POST['user_name']
    date_limit = request.POST['date_limit']

    cur = db.cursor()

    submit_info = []
    info = (static_port, des_ip, des_port, user_name, date_limit)
    submit_info.append(info)
    query = "INSERT INTO static_port_forwarding_apply(static_port, des_ip, des_port, user_name, date_limit) VALUES (%s,%s,%s,%s,%s)"
    cur.executemany(query, submit_info)
    db.commit()

    cur.close()

    return redirect('static_apply_list')


def apply_ok(request):

    static_port = request.POST['static_port']
    des_ip = request.POST['des_ip']
    des_port = request.POST['des_port']
    user_name = request.POST['user_name']
    date_limit = request.POST['date_limit']

    cur = db.cursor()

    submit_info = []
    apply_info = (static_port, des_ip, des_port, user_name, date_limit)
    submit_info.append(apply_info)

    query = "INSERT INTO static_port_forwarding_info(static_port, des_ip, des_port, user_name, date_limit) VALUES (%s,%s,%s,%s,%s)"
    cur.executemany(query, submit_info)

    query = "DELETE FROM static_port_forwarding_apply WHERE static_port=" + static_port
    cur.execute(query)

    db.commit()

    ProxyManager.instance().add_static_proxy(static_port, des_ip, des_port)

    data = {'message': '신청을 승인하였습니다.'}

    return JsonResponse(data)


def apply_reject(request):

    port_number = request.POST['static_port']

    cur = db.cursor()

    query = "DELETE FROM static_port_forwarding_apply WHERE static_port=" + port_number

    cur.execute(query)
    cur.close()

    db.commit()

    data = {"message": "신청을 거절했습니다."}

    return JsonResponse(data)



