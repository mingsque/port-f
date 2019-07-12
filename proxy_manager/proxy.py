import threading
import socket
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from threading import Lock
import json


class Connection:

    def __init__(self, src_socket, des_socket):
        self.src_socket = src_socket
        self.des_socket = des_socket

        self.in_data = 0
        self.out_data = 0

    def send_socket(self):

        while True:
            try:
                data = self.src_socket.recv(2048)
            except Exception as ex:
                print("에러 : {}".format(ex))
                break

            #with self.lock:
            self.in_data = self.in_data + len(data)
            # print("in_data 전송량 : {}".format(self.in_data))

            if data == b"":
                print("src_socket disconnected")
                self.des_socket.close()
                break
            else:
                try:
                    self.des_socket.sendall(data)
                except Exception as ex:
                    print("에러 : {}".format(ex))

    def recv_socket(self):

        while True:
            try:
                received = self.des_socket.recv(2048)
            except:
                print("recv_socket : 소켓이 닫힘")
                break

            #with self.lock:
            self.out_data = self.out_data + len(received)
            # print("out_data 전송량 : {}".format(self.out_data))

            if received == b"":
                self.src_socket.close()
                print("des_socket disconnected")
                break
            else:
                try:
                    self.src_socket.sendall(received)
                except:
                    print("recv_socket_sendall : 소켓이 닫힘")

    def start(self):
        send_thread = threading.Thread(target=self.send_socket)
        recv_thread = threading.Thread(target=self.recv_socket)

        send_thread.start()
        recv_thread.start()

        send_thread.join()
        recv_thread.join()

    def stop(self):
        try:
            self.src_socket.close()
            self.des_socket.close()
        except:
            print("Connection Stop : 이미 닫힌 소켓입니다")

    def __del__(self):
        print("Connection in proxy Destroy")


class Proxy:

    listen_socket = None
    src_socket = None

    listen_ip = '10.1.2.18'
    listen_port = None

    des_socket = None

    des_ip = None
    des_port = None

    in_data = None
    out_data = None

    lock = Lock()

    connection_list = list()

    def set_des(self, des_ip, des_port):

        self.des_ip = des_ip
        self.des_port = int(des_port)

    def listen_start(self):
        print("listening...")
        threading.Thread(target=self.accept_socket).start()

    def listen_stop(self):

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'target': 'listening',
                                                                       'proxy_number': self.no,
                                                                       'status': 'not listening'}})
        try:
            self.listen_socket.close()
        except:
            print("listen_stop : 이미 닫힌 소켓입니다.")

    def connection(self, src_socket, des_socket):

        connection = Connection(src_socket, des_socket)

        self.connection_list.append(connection)

        connection.start()

        self.connection_list.remove(connection)

    def stop(self):
        for connection in self.connection_list:
            connection.stop()

        self.listen_socket.close()

    def listen_status(self):

        return self.listen_flag

    def __del__(self):
        print("proxy instance free by gc_collect")


class StaticProxy(Proxy):

    def __init__(self, port):
        self.listen_port = int(port)

    def accept_socket(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.listen_ip, self.listen_port))
        self.listen_socket.listen()

        while True:
            try:
                src_socket, src_info = self.listen_socket.accept()
            except:
                print("Listening 소켓이 닫힘")
                break
            else:
                des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                des_socket.connect((self.des_ip, self.des_port))

                connection_thread = threading.Thread(target=self.connection, args=(src_socket, des_socket))
                connection_thread.daemon = True
                connection_thread.start()


class DynamicProxy(Proxy):

    def __init__(self, no, port):
        self.listen_flag = 'not listening'
        self.timer_use_yn = 'y'
        self.timer = None
        self.no = no
        self.listen_port = port

    def accept_socket(self):

        channel_layer = get_channel_layer()

        self.listen_flag = 'listening'

        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'target': 'listening',
                                                                       'proxy_number': self.no,
                                                                       'status': 'listening'}})

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.listen_ip, self.listen_port))
        self.listen_socket.listen()

        if self.timer_use_yn == 'y':
            self.timer = threading.Timer(10.0, self.listen_stop)
            self.timer.start()

        while True:
            try:
                src_socket, src_info = self.listen_socket.accept()
            except Exception as ex:
                print("에러 : {}".format(ex))
                break
            else:
                des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                des_socket.connect((self.des_ip, self.des_port))

                connection_thread = threading.Thread(target=self.connection, args=(src_socket, des_socket))
                connection_thread.start()

        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'target': 'listening',
                                                                       'proxy_number': self.no,
                                                                       'status': 'not listening'}})

        self.timer.cancel()

        self.listen_flag = 'not listening'
        self.listen_socket.close()

        print("dynamic proxy close")


class NodeProxy(Proxy):

    def __init__(self, cmd_socket, port):
        self.cmd_socket = cmd_socket
        self.des_socket = None
        self.listen_port = port
        self.des_ip = None
        self.des_port = None
        self.src_socket = None

    def set_des(self, des_ip, des_port):
        self.des_ip = des_ip
        self.des_port = des_port

    def set_des_socket(self, des_socket):
        self.des_socket = des_socket

    def accept_socket(self):

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.listen_ip, self.listen_port))
        self.listen_socket.listen()

        while True:
            self.src_socket, src_info = self.listen_socket.accept()

            send_info = {'command': 'set', 'des_ip': self.des_ip, 'des_port': int(self.des_port)}
            self.cmd_socket.sendall(json.dumps(send_info).encode())

    def stop(self):
        for connection in self.connection_list:
            connection.stop()

        self.listen_socket.close()
        self.cmd_socket.close()

    def __del__(self):
        print("proxy instance free by gc_collect")




