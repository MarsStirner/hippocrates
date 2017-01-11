# -*- coding: utf-8 -*-

import itertools
import logging

from nemesis.app import app
from ..xform import XForm, wrap_simplify, none_default, Undefined, ALREADY_PRESENT_ERROR
from .schemas import ClientSchema

from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_date, safe_traverse
from nemesis.models.client import Client, ClientDocument, ClientPolicy, BloodHistory, \
    ClientAllergy, ClientIntoleranceMedicament, ClientAddress, Address, AddressHouse
from nemesis.models.enums import AddressType

from nemesis.models.exists import rbDocumentType, rbPolicyType, rbBloodType
from nemesis.models.organisation import Organisation
from nemesis.systemwide import db


__author__ = 'viruzzz-kun'

logger = logging.getLogger('simple')


class ClientXForm(ClientSchema, XForm):
    """
    Класс-преобразователь для пациентки
    """
    parent_id_required = False
    target_obj_class = Client

    def _find_target_obj_query(self):
        return Client.query.filter(Client.id == self.target_obj_id, Client.deleted == 0)

    def check_duplicate(self, data):
        fn = data['FIO']['name']
        ln = data['FIO']['surname']
        pn = data['FIO'].get('middlename') or ''
        bd = safe_date(data['birthday_date'])

        q = db.session.query(Client).filter(
            Client.firstName == fn,
            Client.lastName == ln,
            Client.birthDate == bd,
            Client.deleted == 0,
        )
        is_document_required = safe_traverse(
            app.config, 'system_prefs', 'integration',
            'client', 'document_required',
        )
        if is_document_required is None:
            is_document_required = True
        if is_document_required:
            doc_type_code = data['document']['document_type_code']
            self._check_rb_value('rbDocumentType', doc_type_code)
            doc_number = data['document']['document_number']
            q = q.join(ClientDocument).join(rbDocumentType).filter(
                rbDocumentType.TFOMSCode == doc_type_code,
                ClientDocument.number == doc_number,
                ClientDocument.deleted == 0
            )
        if pn:
            q = q.filter(Client.patrName == pn)
        target_obj_exist_id = q.value(Client.id)
        if target_obj_exist_id:
            if is_document_required:
                raise ApiException(
                    ALREADY_PRESENT_ERROR,
                    (u'Уже существует пациент со следующими данными: '
                     u'имя - {0}, фамилия - {1}, отчество - {2}, дата рождения - {3},'
                     u'номер документа - {4}').format(
                        fn, ln, pn, bd, doc_number
                    ),
                    client_id=str(target_obj_exist_id)
                )
            else:
                raise ApiException(
                    ALREADY_PRESENT_ERROR,
                    u'Уже существует пациент со следующими данными: '
                    u'имя - {0}, фамилия - {1}, отчество - {2}, дата рождения - {3},'
                        .format(
                        fn, ln, pn, bd
                    ),
                    client_id=str(target_obj_exist_id)
                )

    def load_data(self):
        if self.new:
            client = Client()
            db.session.add(client)
        else:
            client = self.find_client(self.target_obj_id)
        self.target_obj = client

    def update_client(self, data):
        self.load_data()
        with db.session.no_autoflush:
            self._update_main_data(data)
            if 'document' in data:
                self._update_id_document(data['document'])
            if 'insurance_documents' in data:
                self._update_policies(data['insurance_documents'])
            if 'registration_address' in data:
                self._update_address(data['registration_address'], AddressType.reg[0])
            if 'residential_address' in data:
                self._update_address(data['residential_address'], AddressType.live[0])
            if 'blood_type_info' in data:
                self._update_blood(data['blood_type_info'])
            if 'allergies_info' in data:
                self._update_allergies(data['allergies_info'])
            if 'medicine_intolerance_info' in data:
                self._update_intolerances(data['medicine_intolerance_info'])

    def _update_main_data(self, data):
        client = self.target_obj
        client.firstName = data['FIO']['name']
        client.lastName = data['FIO']['surname']
        client.patrName = data['FIO'].get('middlename') or ''
        client.birthDate = safe_date(data['birthday_date'])
        client.sexCode = data['gender']
        snils = data.get('SNILS')
        client.SNILS = snils.replace('-', '') if snils else ''
        self._changed.append(client)

    def _update_id_document(self, data):
        client = self.target_obj
        self._check_rb_value('rbDocumentType', data['document_type_code'])
        doc_type = rbDocumentType.query.filter(rbDocumentType.TFOMSCode == data['document_type_code']).first()
        document = client.document
        if not document:
            document = ClientDocument()
            document.client = client
        document.documentType = doc_type
        document.serial = data.get('document_series') or ''
        document.number = data['document_number']
        document.date = safe_date(data['document_beg_date'])
        document.origin = data.get('document_issuing_authority') or ''
        self._changed.append(document)

    def _update_policies(self, policies):
        client = self.target_obj
        rbpt_map = dict(
            (str(item.TFOMSCode) or item.code, item)
            for item in rbPolicyType.query
            if item.TFOMSCode
        )

        client_policies = client.policies.all()

        for pol_data, policy in itertools.izip_longest(policies, client_policies):
            if not pol_data:
                policy.deleted = 1
                self._changed.append(policy)
                continue
            pol_type_code = str(pol_data['insurance_document_type'])
            self._check_rb_value('rbPolicyType', pol_type_code)
            policy_type = rbpt_map.get(pol_type_code) or rbpt_map.get('vmi')
            org = self.find_org(pol_data['insurance_document_issuing_authority'])
            if not policy:
                policy = ClientPolicy()
                policy.client = client
            policy.policyType = policy_type
            policy.serial = pol_data.get('insurance_document_series') or ''
            policy.number = pol_data['insurance_document_number']
            policy.begDate = safe_date(pol_data['insurance_document_beg_date'])
            policy.insurer = org
            self._changed.append(policy)

    def _update_address(self, data, type_):
        client = self.target_obj
        client_address = client.loc_address
        if not client_address:
            client.loc_address = client_address = ClientAddress()

        address = client_address.address
        if not address:
            address = client_address.address = Address()

        house = address.house
        if not house:
            house = address.house = AddressHouse()

        house.KLADRStreetCode = data['KLADR_street']
        house.KLADRCode = data['KLADR_locality']
        house.number = data['house']
        house.corpus = data.get('building', '')
        address.flat = data.get('flat')
        client_address.localityType = data.get('locality_type')
        client_address.type = type_
        self._changed.extend([client_address, address, house])

    def _update_blood(self, data_list):
        blood_types = dict(
            (bt.code, bt)
            for bt in rbBloodType.query
        )
        client = self.target_obj
        for blood_data, blood_object in itertools.izip_longest(data_list, client.blood_history):
            if not blood_data:
                blood_object.deleted = 1
                self._changed.append(blood_object)
                continue
            if not blood_object:
                blood_object = BloodHistory()
                blood_object.client = client
            bt_code = blood_data['blood_type']
            self._check_rb_value('rbBloodType', bt_code)
            blood_object.bloodType = blood_types[bt_code]
            self._changed.append(blood_object)

    def _update_allergies(self, data_list):
        client = self.target_obj
        for allergy_data, allergy_object in itertools.izip_longest(data_list, client.allergies):
            if not allergy_data:
                allergy_object.deleted = 1
                self._changed.append(allergy_object)
                continue
            if not allergy_object:
                allergy_object = ClientAllergy()
                allergy_object.client = client
            allergy_object.name = allergy_data['allergy_substance']
            allergy_object.power = allergy_data['allergy_power']
            self._changed.append(allergy_object)

    def _update_intolerances(self, data_list):
        client = self.target_obj
        for intolerance_data, intolerance_object in itertools.izip_longest(data_list, client.intolerances):
            if not intolerance_data:
                intolerance_object.deleted = 1
                self._changed.append(intolerance_object)
                continue
            if not intolerance_object:
                intolerance_object = ClientIntoleranceMedicament()
                intolerance_object.client = client
            intolerance_object.name = intolerance_data['medicine_substance']
            intolerance_object.power = intolerance_data['medicine_intolerance_power']
            self._changed.append(intolerance_object)

    @wrap_simplify
    def as_json(self):
        client = self.target_obj
        return {
            'client_id': self.target_obj.id,
            'FIO': {
                'name': client.firstName,
                'middlename': client.patrName or Undefined,
                'surname': client.lastName,
            },
            'birthday_date': client.birthDate,
            'SNILS': client.SNILS or Undefined,
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
            "document_series": doc.serial or Undefined,
            "document_number": doc.number,
            "document_beg_date": doc.date,
            "document_issuing_authority": doc.origin or Undefined,
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
            "insurance_document_series": doc.serial or Undefined,
            "insurance_document_number": doc.number,
            "insurance_document_beg_date": doc.begDate,
            "insurance_document_issuing_authority": doc.insurer.TFOMSCode if doc.insurer else None,
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
            "building": address.corpus or Undefined,
            "flat": address.flat or Undefined,
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
            "medicine_intolerance_power": intolerance.power,
            "medicine_substance": intolerance.name,
        }

    def delete_target_obj_data(self):
        """
        Dmitry Paschenko, [11.10.16 17:34]
        как правильно удалить пациента в рисар?

        Евгений Коняев, [11.10.16 17:35]
        deleted = 1 пациенту и всем вложенным сущностям, плюс всем связанным event

        Евгений Коняев, [11.10.16 17:35]
        подозреваю, что достаточно будет пациенут и event, но это не точно
        """
        self._find_target_obj_query().update({
            'deleted': 1,
        })
