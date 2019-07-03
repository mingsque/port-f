import threading
import socket
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from threading import Lock


class Connection:

    def __init__(self, src_socket, des_socket):
        self.src_socket = src_socket
        self.des_socket = des_socket

    def __del__(self):
        print("connection in proxy destroy")


class Proxy:
    #no 0 = static, 1~5 = dynamic
    def __init__(self, no, port):

        self.host = "127.0.0.1"
        self.lock = Lock()

        self.no = no
        self.port = int(port)

        self.des_ip = None
        self.des_port = None

        self.listen_socket = None
        self.listen_flag = 'not listening'

        self.in_data = 0
        self.out_data = 0

        self.connections = list()

    def set_des(self, des_ip, des_port):

        self.des_ip = des_ip
        self.des_port = int(des_port)

    def connection(self, src_socket, des_socket):

        connection_socket_info = Connection(src_socket, des_socket)
        self.connections.append(connection_socket_info)

        send_socket_thread = threading.Thread(target=self.send_socket, args=(src_socket, des_socket))
        recv_socket_thread = threading.Thread(target=self.recv_socket, args=(src_socket, des_socket))

        send_socket_thread.start()
        recv_socket_thread.start()

        send_socket_thread.join()
        recv_socket_thread.join()

        self.connections.remove(connection_socket_info)

    def listen_start(self):
        print("listening...")

        connection_thread = threading.Thread(target=self.make_connection)
        connection_thread.daemon = True
        connection_thread.start()

    def listen_stop(self):

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'proxy_number': self.no,
                                                                       'listening_status': 'not listening'}})
        try:
            self.listen_socket.close()
        except:
            print("listen_stop : 이미 닫힌 소켓입니다.")

    def static_listen_start(self):
        print("static listening...")

        listening_thread = threading.Thread(target=self.static_make_connection)
        listening_thread.daemon = True
        listening_thread.start()

    def static_make_connection(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.host, self.port))
        self.listen_socket.listen()

        while True:
            try:
                src_socket, src_info = self.listen_socket.accept()
            except:
                print("소켓이 닫힘")
                break
            else:
                des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                des_socket.connect((self.des_ip, self.des_port))

                connection_thread = threading.Thread(target=self.connection, args=(src_socket, des_socket))
                connection_thread.daemon = True
                connection_thread.start()

    def make_connection(self):

        channel_layer = get_channel_layer()
        self.listen_flag = 'listening'

        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'proxy_number': self.no,
                                                                       'listening_status': 'listening'}})

        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.host, self.port))
        self.listen_socket.listen()

        timer = threading.Timer(10.0, self.listen_stop)
        timer.start()

        try:
            src_socket, src_info = self.listen_socket.accept()
        except Exception as ex:
            print("에러 : {}".format(ex))
            pass
        else:
            des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            des_socket.connect((self.des_ip, self.des_port))

            send_socket_thread = threading.Thread(target=self.send_socket, args=(src_socket, des_socket))
            recv_socket_thread = threading.Thread(target=self.recv_socket, args=(src_socket, des_socket))

            send_socket_thread.daemon = True
            recv_socket_thread.daemon = True

            send_socket_thread.start()
            recv_socket_thread.start()

        timer.cancel()
        async_to_sync(channel_layer.group_send)('status', {'type': 'share_message',
                                                           'message': {'proxy_number': self.no,
                                                                       'listening_status': 'not listening'}})

        self.listen_flag = 'not listening'
        self.listen_socket.close()

        print("dynamic proxy close")

    def send_socket(self, src_socket, des_socket):

        print("destip:{}".format(self.des_ip))
        print("destport:{}".format(self.des_port))
        while True:
            try:
                data = src_socket.recv(2048)
            except:
                print("send_socket : 소켓이 닫힘")
                break

            with self.lock:
                self.in_data = self.in_data + len(data)
            print("in_data 전송량 : {}".format(self.in_data))

            if data == b"":
                print("src_socket disconnected")
                des_socket.close()
                break
            else:
                try:
                    des_socket.sendall(data)
                except:
                    print("send_socket_sendall : 소켓이 닫힘")

    def recv_socket(self, src_socket, des_socket):

        while True:
            try:
                received = des_socket.recv(2048)
            except:
                print("recv_socket : 소켓이 닫힘")
                break

            with self.lock:
                self.out_data = self.out_data + len(received)
            print("out_data 전송량 : {}".format(self.out_data))

            if received == b"":
                src_socket.close()
                print("des_socket disconnected")
                break
            else:
                try:
                    src_socket.sendall(received)
                except:
                    print("recv_socket_sendall : 소켓이 닫힘")

    def static_listen_stop(self):
        for connection in self.connections:
            try:
                connection.des_socket.close()
                connection.src_socket.close()
            except:
                print("static listen_stop : 이미 닫힌 소켓입니다")

        self.listen_socket.close()

    def listen_status(self):

        return self.listen_flag

    def __del__(self):
        print("proxy instance free by gc_collect")