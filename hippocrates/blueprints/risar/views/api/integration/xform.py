# -*- coding: utf-8 -*-
import functools

import datetime

import itertools

import jsonschema
from dateutil.parser import parse as date_parse

from blueprints.risar.views.api.integration.schemas import ClientSchema
from nemesis.lib.apiutils import ApiException
from nemesis.models.client import Client, ClientIdentification, ClientDocument, ClientPolicy, BloodHistory, \
    ClientAllergy, ClientIntoleranceMedicament, ClientAddress, Address, AddressHouse

from nemesis.models.exists import rbAccountingSystem, rbDocumentType, rbPolicyType, rbBloodType
from nemesis.models.organisation import Organisation
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


def none_default(function=None, default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 0 and args[-1] is None:
                if callable(default):
                    return default()
            else:
                return func(*args, **kwargs)
        return wrapper
    if callable(function):
        return decorator(function)
    return decorator


class XForm(object):
    version = 0

    def set_version(self, version):
        for v in xrange(self.version + 1, version + 1):
            method = getattr(self, 'set_version_%i' % v, None)
            if method is None:
                raise ApiException(400, 'Version %i of API is unsupported' % (version, ))
            else:
                method()
        self.version = version


class ClientXForm(XForm, ClientSchema):
    """
    Класс-преобразователь для пациентки
    """
    client = None
    new = False
    rbAccountingSystem = None
    external_system_id = None
    external_client_id = None

    def set_external_system(self, external_system_id):
        self.external_system_id = external_system_id
        self.rbAccountingSystem = rbAS = rbAccountingSystem.query.filter(rbAccountingSystem.code == external_system_id).first()
        if not rbAS:
            raise ApiException(404, 'External system not found')

    def _find_client_query(self, external_client_id):
        if not self.rbAccountingSystem:
            raise Exception('rbAccountingSystem not set')
        return Client.query.join(ClientIdentification).filter(
            ClientIdentification.identifier == external_client_id,
            ClientIdentification.accountingSystems == self.rbAccountingSystem,
        )

    def find_client(self, external_client_id=None, data=None):
        self.external_client_id = external_client_id
        if external_client_id is None:
            # Нас просят создать пациента, но мы должны убедиться, что с таким ИД пациента ещё нет

            # Ручная валидация
            if data is None:
                raise Exception('ClientXForm.find_client called for creation without "data"')

            if 'patient_external_code' not in data:
                raise ApiException(406, 'Validation error', errors=[{
                    'error': '"patient_external_code" is required',
                    'instance': data,
                    'path': '/',
                }])

            # Ищем клиента
            self.external_client_id = external_client_id = data['patient_external_code']
            if self._find_client_query(external_client_id).count():
                raise ApiException(400, u'Client already registered')
                # self.client = self._find_client_query(external_client_id).first()
            client = Client()
            db.session.add(client)
            self.new = True
        else:
            client = self._find_client_query(external_client_id).first()
            if not client:
                raise ApiException(404, u'Client not found')
        self.client = client

    def validate(self, data):
        if data is None:
            raise ApiException(400, 'No JSON body')
        schema = self.schema[self.version]
        cls = jsonschema.validators.validator_for(schema)
        val = cls(schema)
        errors = [{
            'error': error.message,
            'instance': error.instance,
            'path': '/' + '/'.join(map(unicode, error.absolute_path)),
        } for error in val.iter_errors(data)]
        if errors:
            raise ApiException(
                406,
                'Validation error',
                errors=errors,
            )

    def update_client(self, data):
        with db.session.no_autoflush:
            self._update_main_data(data)
            self._update_id_document(data['document'])
            self._update_policies(data['insurance_documents'])
            self._update_address(data['residential_address'])
            self._update_blood(data['blood_type_info'])
            self._update_allergies(data['allergies_info'])
            self._update_intolerances(data['medicine_intolerance_info'])

    def _update_main_data(self, data):
        client = self.client
        client.firstName = data['FIO']['name']
        client.lastName = data['FIO']['surname']
        client.patrName = data['FIO'].get('middlename')
        client.birthDate = date_parse(data['birthday_date'])
        client.sexCode = data['gender']
        client.SNILS = data['SNILS'].replace('-', '')
        ident = client.identifications.filter(ClientIdentification.accountingSystems == self.rbAccountingSystem).first()
        if not ident:
            ident = ClientIdentification()
            ident.accountingSystems = self.rbAccountingSystem
            ident.checkDate = datetime.date.today()
            ident.client = client
            db.session.add(ident)
        ident.identifier = data.get('patient_external_code', self.external_client_id)

    def _update_id_document(self, data):
        client = self.client
        doc_type = rbDocumentType.query.filter(rbDocumentType.TFOMSCode == data['document_type_code']).first()
        document = client.documents.filter(ClientDocument.documentType == doc_type).first()
        if not document:
            document = ClientDocument()
            document.client = client
            db.session.add(document)
        document.documentType = doc_type
        document.serial = data['document_series']
        document.number = data['document_number']
        document.date = data['document_beg_date']
        document.origin = data['document_issuing_authority']

    def _update_policies(self, policies):
        client = self.client
        rbpt_map = dict(
            (str(item.TFOMSCode) or item.code, item)
            for item in rbPolicyType.query
        )

        client_policies = client.policies.all()

        for pol_data, policy in itertools.izip_longest(policies, client_policies):
            if not pol_data:
                policy.deleted = 1
                continue
            policy_type = rbpt_map.get(str(pol_data['insurance_document_type'])) or rbpt_map.get('vmi')
            org = Organisation.query.filter(Organisation.INN == pol_data['insurance_document_issuing_authority']).first()
            if not policy:
                policy = ClientPolicy()
                policy.client = client
                db.session.add(policy)
            policy.policyType = policy_type
            policy.serial = pol_data.get('insurance_document_series', '')
            policy.number = pol_data['insurance_document_number']
            policy.begDate = pol_data['insurance_document_beg_date']
            policy.insurer = org

    def _update_address(self, data):
        client = self.client
        client_address = client.loc_address
        if not client_address:
            client.loc_address = client_address = ClientAddress()
            db.session.add(client_address)

        address = client_address.address
        if not address:
            address = client_address.address = Address()
            db.session.add(address)

        house = address.house
        if not house:
            house = address.house = AddressHouse()
            db.session.add(house)

        house.KLADRStreetCode = data['KLADR_street']
        house.KLADRCode = data['KLADR_locality']
        house.number = data['house']
        house.corpus = data.get('building', '')
        address.flat = data.get('flat')
        client_address.localityType = data.get('locality_type')
        client_address.type = 1

    def _update_blood(self, data_list):
        blood_types = dict(
            (bt.name, bt)
            for bt in rbBloodType.query
        )
        client = self.client
        for blood_data, blood_object in itertools.izip_longest(data_list, client.blood_history):
            if not blood_data:
                blood_object.deleted = 1
                continue
            if not blood_object:
                blood_object = BloodHistory()
                blood_object.client = client
                db.session.add(blood_object)
            blood_object.bloodType = blood_types[blood_data['blood_type']]

    def _update_allergies(self, data_list):
        client = self.client
        for allergy_data, allergy_object in itertools.izip_longest(data_list, client.allergies):
            if not allergy_data:
                allergy_object.deleted = 1
                continue
            if not allergy_object:
                allergy_object = ClientAllergy()
                allergy_object.client = client
                db.session.add(allergy_object)
            allergy_object.name = allergy_data['allergy_substance']
            allergy_object.power = allergy_data['allergy_power']

    def _update_intolerances(self, data_list):
        client = self.client
        for intolerance_data, intolerance_object in itertools.izip_longest(data_list, client.intolerances):
            if not intolerance_data:
                intolerance_object.deleted = 1
                continue
            if not intolerance_object:
                intolerance_object = ClientIntoleranceMedicament()
                intolerance_object.client = client
                db.session.add(intolerance_object)
            intolerance_object.name = intolerance_data['medicine_substance']
            intolerance_object.power = intolerance_data['medicine_intolerance__power']

    def as_json(self):
        client = self.client
        return {
            'id': client.id,
            'FIO': {
                'name': client.firstName,
                'middlename': client.patrName,
                'surname': client.lastName,
            },
            'birthday_date': client.birthDate,
            'gender': client.sexCode,
            'document': self._represent_document(client.document),
            'insurance_documents': map(self._represent_policy, client.policies_all),
            'residential_address': self._represent_residential_address(client.loc_address),
            'blood_type_info': map(self._represent_blood_type, client.blood_history),
            'allergies_info': map(self._represent_allergy, client.allergies),
            'medicine_intolerance_info': map(self._represent_intolerance, client.intolerances),
        }

    @none_default
    def _represent_document(self, doc):
        """
        :type doc: nemesis.models.client.ClientDocument
        :param doc:
        :return:
        """
        return {
            "document_type_code": doc.documentType.TFOMSCode,
            "document_series": doc.serial,
            "document_number": doc.number,
            "document_beg_date": doc.date,
            "document_issuing_authority": doc.origin,
        }

    @none_default
    def _represent_policy(self, doc):
        """
        :type doc: nemesis.models.client.ClientPolicy
        :param doc:
        :return:
        """
        return {
            "insurance_document_type": doc.policyType.TFOMSCode,
            "insurance_document_series": doc.serial,
            "insurance_document_number": doc.number,
            "insurance_document_beg_date": doc.begDate,
            "insurance_document_issuing_authority": doc.insurer.INN if doc.insurer else None,
        }

    @none_default
    def _represent_residential_address(self, address):
        """
        :type address: nemesis.models.client.ClientAddress
        :param address:
        :return:
        """
        return {
            "KLADR_locality": address.KLADRCode,
            "KLADR_street": address.KLADRStreetCode,
            "house": address.number,
            "building": address.corpus,
            "flat": address.flat,
            "locality_type": address.localityType
        }

    @none_default
    def _represent_blood_type(self, blood):
        """
        :type blood: nemesis.models.client.BloodHistory
        :param blood:
        :return:
        """
        return {
            "blood_type": blood.bloodType.name,
        }

    @none_default
    def _represent_allergy(self, allergy):
        """
        :type allergy: nemesis.models.client.ClientAllergy
        :param allergy:
        :return:
        """
        return {
            "allergy_power": allergy.power,
            "allergy_substance": allergy.name,
        }

    @none_default
    def _represent_intolerance(self, intolerance):
        """
        :type intolerance: nemesis.models.client.ClientIntoleranceMedicament
        :param intolerance:
        :return:
        """
        return {
            "medicine_intolerance__power": intolerance.power,
            "medicine_substance": intolerance.name,
        }

    @none_default
    def _represent_patient_external_code(self, client):
        """
        :type client: nemesis.models.client.Client
        :param client:
        :return:
        """
        ident = client.identifications.join(rbAccountingSystem).filter(rbAccountingSystem.code == 'Mis-Bars').first()
        if ident:
            return ident.identifier

