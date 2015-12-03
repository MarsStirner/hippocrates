# -*- coding: utf-8 -*-
import functools

from nemesis.models.client import Client
from nemesis.models.exists import rbAccountingSystem

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


class ClientXForm(object):
    def __init__(self, client=None):
        self.client = client or Client()

    def __json__(self):
        client = self.client
        return {
            'id': client.id,
            'FIO': client.nameText,
            'birthday_date': client.birthDate,
            'gender': client.sexCode,
            'document': self._represent_document(client.document),
            'insurance_documents': map(self._represent_policy, client.policies_all),
            'residental_address': self._represent_residental_address(client.loc_address),
            'blood_type_info': map(self._represent_blood_type, client.blood_history),
            'allergies_info': map(self._represent_intolerance, client.allergies),
            'medicine_intolerance_info': map(self._represent_intolerance, client.intolerances),
            'patient_external_code': self._represent_patient_external_code(client),
            'MIS_external_code': 'Mis-Bars',
            'transfering_data_method_version': 0,
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
            "document_type_code": doc.policyType.TFOMSCode,
            "document_series": doc.serial,
            "document_number": doc.number,
            "document_beg_date": doc.begDate,
            "document_issuing_authority": doc.insurer.INN,
        }

    @none_default
    def _represent_residental_address(self, address):
        """
        :type address: nemesis.models.client.ClientAddress
        :param address:
        :return:
        """
        return {
            "KLADR_locality": address.KLADRCode,
            "KLADR_street": address.KLADRStreetCode,
            "house": ' '.join(filter(None, [address.number, address.corpus])),
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
            "blood_type_assertion_date": blood.bloodDate,
            "blood_type": blood.bloodType.code,
            "bt_doctor_asserted": blood.person_id,
        }

    @none_default
    def _represent_intolerance(self, intolerance):
        """
        :type intolerance: nemesis.models.client.ClientAllergy | nemesis.models.client.ClientIntoleranceMedicament
        :param intolerance:
        :return:
        """
        return {
            "allergy_assertion_date": intolerance.createDate,
            "allergy_power": intolerance.power,
            "allergy_substance": intolerance.name,
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

    def _decode_document(self, doc):
        pass

    def _decode_policy(self, doc):
        pass

    def _decode_address(self, address):
        pass

    def _decode_blood_history(self, history_list):
        pass

    def _decode_blood_type(self, blood_type):
        pass

    def _decode_allergies(self, allergy_list, type):
        pass

    def _decode_allergy(self, allergy, type):
        pass

    def _decode_all(self, data):
        client = self.client

