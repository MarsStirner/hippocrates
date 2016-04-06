# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify, none_default
from .schemas import AnamnesisMotherSchema, AnamnesisFatherSchema
from ..utils import get_action_query

from blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis
from blueprints.risar.lib.utils import get_action_by_id

from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_date, safe_bool, safe_int, safe_dict
from nemesis.models.exists import MKB, rbBloodType


logger = logging.getLogger('simple')


def to_rb(code):
    return {
        'code': code
    } if code is not None else None


def from_rb(rb):
    if rb is None:
        return None
    return rb.code if hasattr(rb, 'code') else rb['code']


def to_mkb_rb(code):
    if code is None:
        return None
    mkb = db.session.query(MKB).filter(MKB.DiagID == code, MKB.deleted == 0).first()
    if not mkb:
        raise ApiException(400, u'Не найден МКБ по коду "{0}"'.format(code))
    return {
        'id': mkb.id,
        'code': code
    }


def from_mkb_rb(rb):
    if rb is None:
        return None
    return rb.DiagID if hasattr(rb, 'DiagID') else rb['code']


def to_blood_type_rb(code):
    if code is None:
        return None
    bt = db.session.query(rbBloodType).filter(rbBloodType.name == code).first()
    if not bt:
        raise ApiException(400, u'Не найдена группа крови по коду "{0}"'.format(code))
    return safe_dict(bt)


def from_blood_type_rb(rb):
    if rb is None:
        return None
    return rb.name if hasattr(rb, 'name') else rb['name']


class AnamnesisMotherXForm(XForm, AnamnesisMotherSchema):
    """
    Класс-преобразователь для документа анамнеза матери
    """

    def __init__(self):
        self.anamnesis = None
        self.pcard = None
        self.new = False

    def find_anamnesis(self, card_id, anamnesis_id=None, data=None):
        pcard = self.find_pcard(card_id)
        self.pcard = pcard

        if anamnesis_id is None:
            # Ручная валидация
            if data is None:
                raise Exception('CardXForm.find_anamnesis called for creation without "data"')

            self.new = True
        else:
            anamnesis = get_action_query(anamnesis_id).first()
            if not anamnesis:
                raise ApiException(404, u'Анамнез с id = {0} не найден'.format(anamnesis_id))
            self.anamnesis = anamnesis

    def convert_and_format(self, data):
        res = {}
        res.update({
            'education': to_rb(data.get('education')),
            'work_group': to_rb(data.get('work_group')),
            'professional_properties': to_rb(data.get('professional_properties')),
            'family_income': to_rb(data.get('family_income')),
            'menstruation_start_age': data.get('menstruation_start_age'),
            'menstruation_duration': data.get('menstruation_duration'),
            'menstruation_period': data.get('menstruation_period'),
            'menstruation_disorders': safe_bool(data.get('menstrual_disorder')),
            'sex_life_start_age': safe_int(data.get('sex_life_age')),
            'fertilization_type': to_rb(data.get('fertilization_type')),
            'intrauterine': safe_bool(data.get('intrauterine_operation')),
            'multifetation': safe_bool(data.get('multiple_fetation')),

            'smoking': safe_bool(data.get('smoking')),
            'alcohol': safe_bool(data.get('alcohol')),
            'toxic': safe_bool(data.get('toxic')),
            'drugs': safe_bool(data.get('drugs')),
            'contraception': map(to_rb, data.get('contraception', [])),
            'hereditary': map(to_rb, data.get('hereditary', [])),

            'finished_diseases_text': data.get('finished_diseases'),
            'current_diseases': map(to_mkb_rb, data.get('current_diseases', [])),

            'menstruation_last_date': safe_date(data.get('last_period_date')),
            'preeclampsia': safe_bool(data.get('preeclampsia_mother_sister')),
            'marital_status': to_rb(data.get('marital_status'))
        })
        if 'infertility' in data:
            res.update({
                'infertility': safe_bool(data['infertility']['infertility_occurence']),
                'infertility_type': to_rb(data['infertility']['infertility_type']),
                'infertility_period': safe_int(data['infertility']['infetrility_duration']),
                'infertility_treatment': map(to_rb, data['infertility']['infertility_treatment']),
                'infertility_cause': map(to_rb, data['infertility']['infertility_causes']),
            })
        return res

    def update_anamnesis(self, data):
        data = self.convert_and_format(data)
        anamnesis = self.anamnesis = get_action_by_id(
            self.anamnesis and self.anamnesis.id, self.pcard.event, risar_mother_anamnesis, True
        )

        for code, value in data.iteritems():
            if code in anamnesis.propsByCode:
                try:
                    prop = anamnesis.propsByCode[code]
                    self.check_prop_value(prop, value)
                    prop.value = value
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise e

    def update_card_attrs(self):
        self.pcard.reevaluate_card_attrs()

    def delete_anamnesis(self):
        self.anamnesis.deleted = 1

    @wrap_simplify
    def as_json(self):
        an_props = self.anamnesis.propsByCode
        return {
            'anamnesis_id': str(self.anamnesis.id),
            'education': from_rb(an_props['education'].value),
            'work_group': from_rb(an_props['work_group'].value),
            'professional_properties': from_rb(an_props['professional_properties'].value),
            'family_income': from_rb(an_props['family_income'].value),
            'menstruation_start_age': an_props['menstruation_start_age'].value,
            'menstruation_duration': an_props['menstruation_duration'].value,
            'menstruation_period': an_props['menstruation_period'].value,
            'menstrual_disorder': an_props['menstruation_disorders'].value,
            'sex_life_age': an_props['sex_life_start_age'].value,
            'fertilization_type': from_rb(an_props['fertilization_type'].value),
            'intrauterine_operation': an_props['intrauterine'].value,
            'multiple_fetation': an_props['multifetation'].value,

            'intertility': self._represent_intertility(),

            'smoking': an_props['smoking'].value,
            'alcohol': an_props['alcohol'].value,
            'toxic': an_props['toxic'].value,
            'drugs': an_props['drugs'].value,
            'contraception': map(from_rb, an_props['contraception'].value),
            'hereditary': map(from_rb, an_props['hereditary'].value),

            'finished_diseases': an_props['finished_diseases_text'].value,
            'current_diseases': map(from_mkb_rb, an_props['current_diseases'].value),

            'last_period_date': an_props['menstruation_last_date'].value,
            'preeclampsia_mother_sister': an_props['preeclampsia'].value,
            'marital_status': from_rb(an_props['marital_status'].value)
        }

    @none_default
    def _represent_intertility(self):
        an_props = self.anamnesis.propsByCode
        return {
            'infertility_occurence': an_props['infertility'].value,
            'infertility_type': from_rb(an_props['infertility_type'].value),
            'infetrility_duration': an_props['infertility_period'].value,
            'infertility_treatment': map(from_rb, an_props['infertility_treatment'].value),
            'infertility_causes': map(from_rb, an_props['infertility_cause'].value)
        }


class AnamnesisFatherXForm(XForm, AnamnesisFatherSchema):
    """
    Класс-преобразователь для документа анамнеза отца
    """

    def __init__(self):
        self.anamnesis = None
        self.pcard = None
        self.new = False

    def find_anamnesis(self, card_id, anamnesis_id=None, data=None):
        pcard = self.find_pcard(card_id)
        self.pcard = pcard

        if anamnesis_id is None:
            # Ручная валидация
            if data is None:
                raise Exception('CardXForm.find_anamnesis called for creation without "data"')

            self.new = True
        else:
            anamnesis = get_action_query(anamnesis_id).first()
            if not anamnesis:
                raise ApiException(404, u'Анамнез с id = {0} не найден'.format(anamnesis_id))
            self.anamnesis = anamnesis

    def convert_and_format(self, data):
        res = {}
        res.update({
            'name': data.get('FIO'),
            'age': safe_int(data.get('age')),
            'education': to_rb(data.get('education')),
            'work_group': to_rb(data.get('work_group')),
            'professional_properties': to_rb(data.get('professional_properties')),
            'phone': data.get('telephone_number'),
            'fluorography': data.get('fluorography'),
            'HIV': safe_bool(data.get('hiv')),
            'blood_type': to_blood_type_rb(data.get('blood_type')),

            'smoking': safe_bool(data.get('smoking')),
            'alcohol': safe_bool(data.get('alcohol')),
            'toxic': safe_bool(data.get('toxic')),
            'drugs': safe_bool(data.get('drugs')),
            'hereditary': map(to_rb, data.get('hereditary', [])),

            'finished_diseases_text': data.get('finished_diseases'),
            'current_diseases_text': data.get('current_diseases'),
        })
        if 'infertility' in data:
            res.update({
                'infertility': safe_bool(data['infertility']['infertility_occurence']),
                'infertility_type': to_rb(data['infertility']['infertility_type']),
                'infertility_period': safe_int(data['infertility']['infetrility_duration']),
                'infertility_treatment': map(to_rb, data['infertility']['infertility_treatment']),
                'infertility_cause': map(to_rb, data['infertility']['infertility_causes']),
            })
        return res

    def update_anamnesis(self, data):
        data = self.convert_and_format(data)
        anamnesis = self.anamnesis = get_action_by_id(
            self.anamnesis and self.anamnesis.id, self.pcard.event, risar_father_anamnesis, True
        )

        for code, value in data.iteritems():
            if code in anamnesis.propsByCode:
                try:
                    prop = anamnesis.propsByCode[code]
                    self.check_prop_value(prop, value)
                    prop.value = value
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise e

    def update_card_attrs(self):
        self.pcard.reevaluate_card_attrs()

    def delete_anamnesis(self):
        self.anamnesis.deleted = 1

    @wrap_simplify
    def as_json(self):
        an_props = self.anamnesis.propsByCode
        return {
            'anamnesis_id': str(self.anamnesis.id),
            'FIO': an_props['name'].value,
            'age': an_props['age'].value,
            'education': from_rb(an_props['education'].value),
            'work_group': from_rb(an_props['work_group'].value),
            'professional_properties': from_rb(an_props['professional_properties'].value),
            'telephone_number': an_props['phone'].value,
            'fluorography': an_props['fluorography'].value,
            'hiv': an_props['HIV'].value,
            'blood_type': from_blood_type_rb(an_props['blood_type'].value),

            'intertility': self._represent_intertility(),

            'smoking': an_props['smoking'].value,
            'alcohol': an_props['alcohol'].value,
            'toxic': an_props['toxic'].value,
            'drugs': an_props['drugs'].value,
            'hereditary': map(from_rb, an_props['hereditary'].value),

            'finished_diseases': an_props['finished_diseases_text'].value,
            'current_diseases': an_props['current_diseases_text'].value
        }

    @none_default
    def _represent_intertility(self):
        an_props = self.anamnesis.propsByCode
        return {
            'infertility_occurence': an_props['infertility'].value,
            'infertility_type': from_rb(an_props['infertility_type'].value),
            'infetrility_duration': an_props['infertility_period'].value,
            'infertility_treatment': map(from_rb, an_props['infertility_treatment'].value),
            'infertility_causes': map(from_rb, an_props['infertility_cause'].value)
        }