import threading
import socket
import json
import time
from threading import Lock
import sys

class Connector:

    def __init__(self, host_ip, host_port):
        self.host_ip = host_ip
        self.host_port = host_port

        self.connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_socket.connect((self.host_ip, self.host_port))

    def get_connect_socket(self):
        return self.connect_socket


class MasterConnector:

    def __init__(self, master_ip, master_port):
        self.master_ip = master_ip
        self.master_port = master_port

        self.connect_socket = Connector(self.master_ip, self.master_port).get_connect_socket()

        self.in_data = 0
        self.out_data = 0

        self.data_socket_list = list()

        recv_data = self.connect_socket.recv(2048)
        commander_info = self.data_to_dict(recv_data)

        send_info = {'message': 'ok'}
        self.connect_socket.sendall(json.dumps(send_info).encode())

        self.lock = Lock()

        self.commander_fd = commander_info['fd']
        self.commander_data_fd_list = list()

    def data_to_dict(self, recv_data):
        return json.loads(recv_data.decode('utf-8'))

    def wait_command(self):

        recv_data = self.connect_socket.recv(2048)
        print("recv command")
        command_info = self.data_to_dict(recv_data)
        print(command_info)
        return command_info

    def make_connect(self):
        data_socket = Connector(self.master_ip, self.master_port).get_connect_socket()
        self.data_socket_list.append(data_socket)


        print("make data socket make")
        recv_data = data_socket.recv(2048)
        command_info = self.data_to_dict(recv_data)

        self.commander_data_fd_list.append(command_info['fd'])

        send_info = {'message': 'set', 'fd': self.commander_fd}
        data_socket.sendall(json.dumps(send_info).encode())
        print(send_info)
        
        return data_socket

    def send_socket(self, src_socket, des_socket):

        while True:
            try:
                data = src_socket.recv(2048)
                print(data)
            except Exception as ex:
                print("에러 : {}".format(ex))
                break

            with self.lock:
                self.in_data = self.in_data + len(data)
            # print("in_data 전송량 : {}".format(self.in_data))

            if data == b"":
                print("src_socket disconnected")
                des_socket.close()
                break
            else:
                try:
                    des_socket.sendall(data)
                except Exception as ex:
                    print("에러 : {}".format(ex))

    def recv_socket(self, src_socket, des_socket):

        while True:
            try:
                received = des_socket.recv(2048)
                print(received)
            except:
                print("recv_socket : 소켓이 닫힘")
                break

            with self.lock:
                self.out_data = self.out_data + len(received)
            # print("out_data 전송량 : {}".format(self.out_data))

            if received == b"":
                src_socket.close()
                print("des_socket disconnected")
                break
            else:
                try:
                    src_socket.sendall(received)
                except:
                    print("recv_socket_sendall : 소켓이 닫힘")


if __name__ == "__main__":

    connector = MasterConnector('127.0.0.1', 8001)

    while True:
        print("wait start")
        command_info = connector.wait_command()
    
        if command_info['command'] == 'set':

            des_ip = command_info['des_ip']
            des_port = command_info['des_port']
            
            src_socket = connector.make_connect()
            time.sleep(1)
            des_socket = Connector(des_ip, des_port).get_connect_socket()
    
            send_socket_thread = threading.Thread(target=connector.send_socket, args=(src_socket, des_socket)).start()
            recv_socket_thread = threading.Thread(target=connector.recv_socket, args=(src_socket, des_socket)).start()
        if command_info['command'] == 'close':
            sys.exit(1)

