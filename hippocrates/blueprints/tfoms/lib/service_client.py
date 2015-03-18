# -*- coding: utf-8 -*-
import os
from datetime import date, timedelta
import calendar

from urlparse import urlparse

from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from thrift_service.TFOMSService import Client
from thrift_service.ttypes import InvalidOrganizationInfisException
from thrift_service.ttypes import InvalidArgumentException, NotFoundException, SQLException, TException, TClientPolicy
from thrift_service.ttypes import Payment, AccountItemWithMark


class TFOMSClient(object):
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

        self.date_tags = ['DR',
                          'DATE_1',
                          'DATE_2',
                          'DATE_IN',
                          'DATE_OUT',
                          'D_R',
                          'DAT_PR',
                          'DAT_VV',
                          'DAT_BLVN',
                          'DAT_ELVN',
                          'date',
                          'begDate',
                          'endDate',
                          'exposeDate',
                          'serviceDate', ]

    def __del__(self):
        self.transport.close()

    def __convert_date(self, timestamp):
        if os.name == 'nt':
            # Hack for Win (http://stackoverflow.com/questions/10588027/converting-timestamps-larger-than-maxint-into-datetime-objects)
            return date.fromtimestamp(0) + timedelta(seconds=timestamp / 1000)
        return date.fromtimestamp(timestamp / 1000)

    def __convert_dates(self, data):
        #TODO: унифицировать для обеих выборок, учесть вложенность
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    for element in item:
                        for attr, value in element.__dict__.iteritems():
                            if attr in self.date_tags and isinstance(value, (int, long)) and value:
                                setattr(element, attr, self.__convert_date(value))
                            elif isinstance(value, basestring):
                                setattr(element, attr, value.strip().decode('utf8'))
                else:
                    for attr, value in item.__dict__.iteritems():
                        if attr in self.date_tags and isinstance(value, (int, long)) and value:
                            setattr(item, attr, self.__convert_date(value))
                        elif isinstance(value, basestring):
                            setattr(item, attr, value.strip().decode('utf8'))
        elif isinstance(data, object):
            for attr, value in data.__dict__.iteritems():
                    if attr in self.date_tags and isinstance(value, (int, long)) and value:
                        setattr(data, attr, self.__convert_date(value))
                    elif isinstance(value, basestring):
                        setattr(data, attr, value.strip().decode('utf8'))
        return data

    def __unicode_result(self, data):
        #TODO: унифицировать для обеих выборок, учесть вложенность
        for element in data:
            for attr, value in element.__dict__.iteritems():
                if isinstance(value, basestring):
                    setattr(element, attr, value.strip().decode('utf8'))
                elif attr in self.date_tags and isinstance(value, (int, long)) and value:
                    setattr(element, attr, self.__convert_date(value))
        return data

    def get_xml_registry(self,
                         contract_id,
                         infis_code,
                         old_infis_code,
                         start,
                         end,
                         smo_number,
                         primary=True,
                         departments=None,
                         mo_level=None,
                         patient_optional=list(),
                         person_optional=list(),
                         event_optional=list()):
        """Получает список пациентов и услуг для XML-выгрузки данном ЛПУ в указанный промежуток времени"""
        result = None
        try:
            result = self.client.getXMLRegisters(contractId=contract_id,
                                                 infisCode=infis_code,
                                                 obsoleteInfisCode=old_infis_code,
                                                 beginDate=calendar.timegm(start.timetuple()) * 1000,
                                                 endDate=calendar.timegm(end.timetuple()) * 1000,
                                                 orgStructureIdList=departments,
                                                 patientOptionalFields=patient_optional,
                                                 personOptionalFields=person_optional,
                                                 sluchOptionalFields=event_optional,
                                                 primaryAccount=primary,
                                                 smoNumber=smo_number,
                                                 levelMO=mo_level)
        except InvalidArgumentException, e:
            print e
            raise e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_departments(self, infis_code):
        """Получает список подразделений в данном ЛПУ"""
        result = None
        try:
            result = self.client.getOrgStructures(organisationInfis=infis_code)
        except InvalidOrganizationInfisException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_contracts(self, infis_code):
        """Получает список доступных контрактов в данном ЛПУ"""
        result = None
        try:
            result = self.client.getAvailableContracts(organisationInfis=infis_code)
        except InvalidOrganizationInfisException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_bills(self, infis_code):
        """Получает список доступных счетов в данном ЛПУ"""
        result = None
        try:
            result = self.client.getAvailableAccounts()
        except InvalidOrganizationInfisException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_bill(self, bill_id):
        """Получает счет по id"""
        result = None
        try:
            result = self.client.getAccount(accountId=bill_id)
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_bill_cases(self, bill_id):
        """Получает список доступных счетов в данном ЛПУ"""
        result = None
        try:
            result = self.client.getAccountItems(accountId=bill_id)
        except InvalidOrganizationInfisException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def change_cases_status(self, data):
        """Смена статусов для позиций счета"""
        result = False
        request = list()
        if isinstance(data, list):
            for case in data:
                account_item = AccountItemWithMark(case['id'], case['status'])
                if 'note' in case and case['note']:
                    account_item.note = case['note']
                request.append(account_item)
        else:
            account_item = AccountItemWithMark(data['id'], data['status'])
            if 'note' in data and data['note']:
                account_item.note = data['note']
            request.append(account_item)
        try:
            self.client.setDoNotUploadAnymoreMarks(request)
        except SQLException, e:
            print e
            return result
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def delete_bill(self, bill_id):
        """Получает список доступных счетов в данном ЛПУ"""
        result = None
        try:
            result = self.client.deleteAccount(accountId=bill_id)
        except InvalidOrganizationInfisException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_patients(self, infis_code, start, end, **kwargs):
        """Получает список пациентов, которому оказаны услуги в данном ЛПУ в указанный промежуток времени"""
        result = None
        try:
            optional = kwargs.get('optional', list())
            result = self.client.getPatients(beginDate=calendar.timegm(start.timetuple()) * 1000,
                                             endDate=calendar.timegm(end.timetuple()) * 1000,
                                             infisCode=infis_code,
                                             optionalFields=optional)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return self.__unicode_result(result)

    def get_patient_events(self, patients, start, end, infis_code, **kwargs):
        """Получает список событий и услуг, оказанных пациенту в указанный промежуток времени"""
        result = None
        try:
            optional = kwargs.get('optional', list())
            result = self.client.getSluchByPatients(patientId=patients,
                                                    beginDate=calendar.timegm(start.timetuple()) * 1000,
                                                    endDate=calendar.timegm(end.timetuple()) * 1000,
                                                    infisCode=infis_code,
                                                    optionalFields=optional)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return self.__convert_dates(result)

    def prepare_tables(self):
        """Запускает процесс обновления данных во временной таблице на сервере"""
        result = None
        try:
            result = self.client.prepareTables()
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def get_policlinic_dbf(self, infis_code, start, end, **kwargs):
        """Получает данные для dbf по поликлинике и стационару в данном ЛПУ в указанный промежуток времени"""
        result = None
        try:
            result = self.client.getDBFPoliclinic(beginDate=calendar.timegm(start.timetuple()) * 1000,
                                                  endDate=calendar.timegm(end.timetuple()) * 1000,
                                                  infisCode=infis_code)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return self.__unicode_result(result)

    def get_hospital_dbf(self, infis_code, start, end, **kwargs):
        """Получает данные для dbf по поликлинике и стационару в данном ЛПУ в указанный промежуток времени"""
        result = None
        try:
            result = self.client.getDBFStationary(beginDate=calendar.timegm(start.timetuple()) * 1000,
                                                  endDate=calendar.timegm(end.timetuple()) * 1000,
                                                  infisCode=infis_code)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return self.__unicode_result(result)

    def update_policy(self, patient_id, data):
        """Обновление полисов у пациентов"""
        result = None
        try:
            if isinstance(data, TClientPolicy):
                for key, value in data.__dict__.iteritems():
                    if isinstance(value, basestring):
                        setattr(data, key, value.encode('utf-8'))
            result = self.client.changeClientPolicy(patientId=patient_id, newPolicy=data)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result

    def load_tfoms_payments(self, data):
        """Отправка данных, полученных из ТФОМС"""
        result = None
        try:
            result = self.client.loadTfomsPayments(**data)
        except InvalidArgumentException, e:
            print e
        except SQLException, e:
            print e
        except NotFoundException, e:
            raise e
        except TException, e:
            raise e
        return result