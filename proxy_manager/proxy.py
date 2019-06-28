import threading
import socketserver
import socket


destination_address = ("192.168.116.130", 22)


class ServerHandler (socketserver.BaseRequestHandler):

    def send_socket(self, src_socket, des_socket):
        while True:
            data = src_socket.recv(2000)
            print("cli:".format(data))
            des_socket.sendall(data)

    def recv_socket(self, src_socket, des_socket):
        while True:
            received = des_socket.recv(2000)
            print("des:{}".format(received))
            src_socket.sendall(received)

    def handle(self):

        src_socket = self.request

        des_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        des_socket.connect(destination_address)

        send_socket_thread = threading.Thread(target=self.send_socket, args=(src_socket, des_socket))
        recv_socket_thread = threading.Thread(target=self.recv_socket, args=(src_socket, des_socket))

        send_socket_thread.start()
        recv_socket_thread.start()

        send_socket_thread.join()
        recv_socket_thread.join()

        print("end...")


#가변포트는 리스닝의 이유가 없다, 원래 리스닝 부분은 디 장고 웹에서 대신 하므로 요청이 들어오면 프록시를 실행시키자
#고정은 필요할듯
class Proxy:

    def __init__(self, port, dest_ip, dest_port):
        self.type = "dynamic"
        self.host = "127.0.0.1"
        #use 10500~10504
        self.port = port
        self.dest_ip = dest_ip
        self.dest_port = dest_port

    def listen_start(self):
        print("listening...")
        server = socketserver.TCPServer((self.host, self.port), ServerHandler)
        server_thread = threading.Thread(target=server.serve_forever())
        server_thread.start()

    def listen_stop(self):
        print("소켓, 스레드 정리")

