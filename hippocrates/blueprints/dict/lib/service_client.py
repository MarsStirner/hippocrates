# -*- coding: utf-8 -*-

from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol
from .thrift_service.TARIFF.ttypes import InvalidArgumentException, SQLException, TException
from urlparse import urlparse
from .thrift_service.TARIFF.TARIFFService import Client


class TARIFFClient(object):
    """Класс клиента для взаимодействия с ядром по Thrift-протоколу"""

    class Struct:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def __init__(self, url):
        self.url = url
        url_parsed = urlparse(self.url)
        host = url_parsed.hostname
        port = url_parsed.port

        socket = TSocket.TSocket(host, port)
        self.transport = TTransport.TBufferedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = Client(protocol)
        self.transport.open()

    def __del__(self):
        self.transport.close()

    def send_tariffs(self, data, contract_id):
        """Отправка тарифов"""
        try:
            result = self.client.updateTariffs(tariffs=data, contract_id=int(contract_id))
        except InvalidArgumentException, e:
            raise e
        except SQLException, e:
            raise e
        except TException, e:
            raise e
        return result