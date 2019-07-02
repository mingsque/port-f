import threading
import socketserver
import socket
import json
from .consumers import StatusConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

destination_address = ("192.168.116.133", 22)


class Connection:
    def __init__(self):
        self.src_ip
        self.src_port
        self.des_ip
        self.des_port
        self.user


#가변포트는 리스닝의 이유가 없다, 원래 리스닝 부분은 디 장고 웹에서 대신 하므로 요청이 들어오면 프록시를 실행시키자
#고정은 필요할듯
class Proxy:

    def __init__(self, no, port):
        self.host = "127.0.0.1"
        #use 10500~10504
        self.port = port
        self.dest_ip = None
        self.dest_port = None

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.host, self.port))

        self.listen_flag = 'not listening'
        self.no = no

    def set_dest(self, dest_ip, dest_port):

        self.dest_ip = dest_ip
        self.dest_port = int(dest_port)

    def listen_start(self):
        print("listening...")

        connection_thread = threading.Thread(target=self.make_connection)
        connection_thread.daemon = True
        connection_thread.start()

    def make_connection(self):

        channel_layer = get_channel_layer()
        self.listen_flag = 'listening'
        print(channel_layer)

        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message', 'message': {'proxy_number': self.no,
                                                                                                'listening_status':'listening'}})
        try:
            self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listen_socket.bind((self.host, self.port))
            self.listen_socket.listen()
            src_socket, src_info = self.listen_socket.accept()
        except Exception as ex:
            print("에러 : {}".format(ex))
            pass
        else:
            des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            des_socket.connect((self.dest_ip, self.dest_port))

            send_socket_thread = threading.Thread(target=self.send_socket, args=(src_socket, des_socket))
            recv_socket_thread = threading.Thread(target=self.recv_socket, args=(src_socket, des_socket))

            send_socket_thread.daemon = True
            recv_socket_thread.daemon = True

            send_socket_thread.start()
            recv_socket_thread.start()

        async_to_sync(channel_layer.group_send)('status',
                                                    {'type': 'share_message', 'message': {'proxy_number': self.no,
                                                                                          'listening_status': 'not listening'}})
        self.listen_flag = 'not listening'
        self.listen_socket.close()

        print("close")

    def send_socket(self, src_socket, des_socket):

        print("destip:{}".format(self.dest_ip))
        print("destport:{}".format(self.dest_port))
        while True:
            data = src_socket.recv(2000)
            if data == b"":
                print("src_socket disconnected")
                des_socket.close()
                break
            else:
                print("cli:".format(data))
                des_socket.sendall(data)

    def recv_socket(self, src_socket, des_socket):
        while True:
            received = des_socket.recv(2000)
            if received == b"":
                src_socket.close()
                print("des_socket disconnected")
                break
            else:
                print("des:{}".format(received))
                src_socket.sendall(received)

    def listen_stop(self):
        print("소켓, 스레드 정리")
        self.listen_socket.close()

    def listen_status(self):

        return self.listen_flag
