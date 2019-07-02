from .proxy import Proxy
from channels.generic.websocket import WebsocketConsumer
import json


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

        self.proxy_list = list()
        self.proxy_list.append(Proxy(1, 10500))
        self.proxy_list.append(Proxy(2, 10501))
        self.proxy_list.append(Proxy(3, 10502))
        self.proxy_list.append(Proxy(4, 10503))
        self.proxy_list.append(Proxy(5, 10504))

    def listen_status(self):
        status = list()
        for proxy in self.proxy_list:
            status.append(proxy.listen_flag)

        return status

    def get_proxy(self, number):
        return self.proxy_list.__getitem__(number-1)

