from .proxy import *
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import MySQLdb
import socket
import threading
import json
import time
import sys

class Singleton:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance

class ProxyManager(Singleton):

    def __init__(self):

        print("ProxyManager On")

        self.default = 20000
        #가변 포트
        self.proxy_list = list()
        self.proxy_list.append(DynamicProxy(1, 30001))
        self.proxy_list.append(DynamicProxy(2, 30002))
        self.proxy_list.append(DynamicProxy(3, 30003))
        self.proxy_list.append(DynamicProxy(4, 30004))
        self.proxy_list.append(DynamicProxy(5, 30005))

        # 고정 포트
        #proxy info in database
        self.static_proxy_info = None
        #listening proxy list
        self.static_proxy_list = list()
        #fd , socket
        self.node_proxy_list = dict()

        self.db = MySQLdb.connect(host="127.0.0.1", user="root", passwd="hamonsoft", db="pilot")
        self.set_proxy_info()
        self.start_schedule()
        self.listen_slave()

    def close_command(self, transfer_info):

        target_proxy = self.node_proxy_list[int(transfer_info['node_proxy_key'])]
        node = target_proxy['node_proxy']

        node.stop()

        del self.node_proxy_list[int(transfer_info['node_proxy_key'])]
        print(self.node_proxy_list)

    def transfer_command(self, transfer_info):

        print("transfer")
        target_proxy = self.node_proxy_list[int(transfer_info['node_proxy_key'])]
        target_proxy['node_proxy'].set_des(transfer_info['des_ip'], transfer_info['des_port'])

    def make_slave_connetion(self):

        slave_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        slave_listen_socket.bind(('10.1.2.18', 8001))
        slave_listen_socket.listen()

        while True:
            slave_data_socket, slave_info = slave_listen_socket.accept()

            info = {'fd': slave_data_socket.fileno()}
            slave_data_socket.sendall(json.dumps(info).encode())

            data = slave_data_socket.recv(2048)

            data = json.loads(data.decode('utf-8'))

            if data['message'] == 'ok':
                print(slave_data_socket.fileno)

                self.default = self.default + 1

                self.slave_proxy = NodeProxy(slave_data_socket, self.default)
                self.node_proxy_list[slave_data_socket.fileno()] = {'node_proxy': self.slave_proxy,
                                                                    'fd': slave_data_socket.fileno(),
                                                                    'connect_time': datetime.now(),
                                                                    'ip_address': slave_info,
                                                                    'listening_port': self.default}

                self.slave_proxy.listen_start()
                print(self.node_proxy_list)

            if data['message'] == 'set':
                target = self.node_proxy_list[data['fd']]['node_proxy']
                print(slave_data_socket)
                target.connection(target.src_socket, slave_data_socket)

            print('no')

    def listen_slave(self):
        threading.Thread(target=self.make_slave_connetion).start()

    def set_proxy_info(self):

        cur = self.db.cursor()

        #get proxy_info from database
        query = "SELECT * FROM static_port_forwarding_info"
        cur.execute(query)
        self.static_proxy_info = cur.fetchall()
        print("Proxy information : {}".format(self.static_proxy_info))

        for proxy_info in self.static_proxy_info:

            proxy = StaticProxy(proxy_info[0])
            proxy.set_des(proxy_info[1], proxy_info[2])
            self.static_proxy_list.append(proxy)
            proxy.listen_start()

        cur.close()

    def del_static_proxy(self, static_port):

        cur = self.db.cursor()

        for proxy in self.static_proxy_list:
            if proxy.port == int(static_port):
                print("remove proxy , running list and database")
                self.static_proxy_list.remove(proxy)
                #destroy proxy , socket close
                proxy.stop()
                query = "DELETE FROM static_port_forwarding_info WHERE static_port = " + str(proxy.port)
                cur.execute(query)
                self.db.commit()
                break

        cur.close()
        self.db.commit()

    def check_data_amount(self):

        cur = self.db.cursor()

        commit_info = []
        for proxy in self.static_proxy_list:

            in_data = proxy.in_data
            out_data = proxy.out_data
            proxy.in_data = 0
            proxy.out_data = 0

            insert_info = (proxy.listen_port, in_data, out_data)
            commit_info.append(insert_info)

        query = """INSERT INTO DATA_USE_AMOUNT (static_port, in_data, out_data) 
                    SELECT A.static_port, A.in_data, A.out_data
                    FROM (SELECT %s AS static_port,
                                 %s AS in_data,
                                 %s AS out_data
                            FROM DUAL
                         )A
                    ON DUPLICATE KEY
                    UPDATE in_data = DATA_USE_AMOUNT.in_data + A.in_data,
                            out_data = DATA_USE_AMOUNT.out_data + A.out_data
                """

        cur.executemany(query, commit_info)
        cur.close()

        self.db.commit()

    def check_destroy_proxy(self):
        cur = self.db.cursor()

        query = "SELECT static_port, update_time FROM data_use_amount"
        cur.execute(query)
        results = cur.fetchall()

        current_time = datetime.now()

        for result in results:
            limit = (current_time - result[1]).days
            print(result[0])
            print(limit)
            if limit > 3:
                self.del_static_proxy(result[0])

        query = "SELECT * FROM static_port_forwarding_info"
        cur.execute(query)
        results = cur.fetchall()

        current_date = current_time.date()

        for result in results:
            limit = (current_date - result[4]).days
            print(limit)
            if limit >= 0:
                self.del_static_proxy(result[0])

        cur.close()

    def start_schedule(self):
        print("Scheduler start")

        scheduler = BackgroundScheduler()
        scheduler.start()

        scheduler.add_job(self.check_data_amount, 'interval', seconds=10, id='data_checker')
        scheduler.add_job(self.check_destroy_proxy, 'interval', days=1, start_date=datetime.now(), id='proxy_remover')

    def listen_status(self):
        status = list()
        for proxy in self.proxy_list:
            info = {'port_number': proxy.listen_port,
                    'listening_state': proxy.listen_flag,
                    'pick_state': proxy.timer_use_yn}

            status.append(info)
        return status

    def get_static_status(self):

        cur = self.db.cursor()

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
        result = cur.fetchall()

        cur.close()

        return result

    def get_static_apply_list(self):

        cur = self.db.cursor()

        query = "SELECT * FROM static_port_forwarding_apply"
        cur.execute(query)

        result = cur.fetchall()

        cur.close()

        return result

    def set_static_apply_submit(self, static_port, des_ip, des_port, user_name, date_limit):

        cur = self.db.cursor()

        submit_info = []
        info = (static_port, des_ip, des_port, user_name, date_limit)
        submit_info.append(info)
        query = "INSERT INTO static_port_forwarding_apply(static_port, des_ip, des_port, user_name, date_limit) VALUES (%s,%s,%s,%s,%s)"
        cur.executemany(query, submit_info)
        self.db.commit()

        cur.close()

        return

    def add_static_proxy(self, static_port, des_ip, des_port, user_name, date_limit):

        cur = self.db.cursor()

        submit_info = []
        apply_info = (static_port, des_ip, des_port, user_name, date_limit)
        submit_info.append(apply_info)

        query = "INSERT INTO static_port_forwarding_info(static_port, des_ip, des_port, user_name, date_limit) VALUES (%s,%s,%s,%s,%s)"
        cur.executemany(query, submit_info)

        query = "DELETE FROM static_port_forwarding_apply WHERE static_port=" + static_port
        cur.execute(query)

        self.db.commit()

        proxy = StaticProxy(0, static_port)
        proxy.set_des(des_ip, des_port)
        proxy.static_listen_start()
        self.static_proxy_list.append(proxy)

        cur.close()

    def get_proxy(self, number):

        return self.proxy_list.__getitem__(number - 1)

    def static_apply_reject(self, static_port):
        cur = self.db.cursor()

        query = "DELETE FROM static_port_forwarding_apply WHERE static_port=" + static_port
        cur.execute(query)

        cur.close()
        self.db.commit()
