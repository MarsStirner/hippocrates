# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify, none_default, ALREADY_PRESENT_ERROR
from .schemas import AnamnesisMotherSchema, AnamnesisFatherSchema, AnamnesisPrevPregSchema

from blueprints.risar.risar_config import risar_mother_anamnesis, risar_father_anamnesis, risar_anamnesis_pregnancy
from blueprints.risar.lib.utils import get_action, get_action_by_id
from blueprints.risar.lib.prev_children import create_or_update_prev_children, get_previous_children
from blueprints.risar.lib.card import PregnancyCard

from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_date, safe_bool, safe_int
from nemesis.models.event import Event
from nemesis.models.actions import Action, ActionType


logger = logging.getLogger('simple')


class AnamnesisXForm(XForm):

    flat_code = None

    def _find_target_obj_query(self):
        return Action.query.join(ActionType).filter(
            Action.deleted == 0,
            Action.event_id == self.parent_obj_id,
            ActionType.flatCode == self.flat_code
        )

    def get_parent_nf_msg(self):
        return u'Не найдена карта с id = {0}'.format(self.parent_obj_id)

    def update_card_attrs(self):
        if self.pcard is None:
            self.pcard = PregnancyCard.get_for_event(self.parent_obj)
        self.pcard.reevaluate_card_attrs()
        self._changed.append(self.pcard.attrs)

    def convert_and_format(self, data):
        return data

    def update_target_obj(self, data):
        data = self.convert_and_format(data)

        event = self.parent_obj = self.find_event(self.parent_obj_id)
        anamnesis = self.target_obj = get_action(event, self.flat_code, True)

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

        self._changed.append(self.target_obj)

    def delete_target_obj(self):
        self.parent_obj = self.find_event(self.parent_obj_id)
        self.target_obj_class.query.join(ActionType, Event).filter(
            self.parent_obj_class.id == self.parent_obj_id,
            ActionType.flatCode == self.flat_code,
            Action.event_id == Event.id,
            Action.actionType_id == ActionType.id
        ).update({self.target_obj_class.deleted: 1})


class AnamnesisMotherXForm(AnamnesisMotherSchema, AnamnesisXForm):
    """
    Класс-преобразователь для документа анамнеза матери
    """
    target_obj_class = Action
    parent_obj_class = Event
    target_id_required = False
    flat_code = risar_mother_anamnesis

    def check_duplicate(self, parent_obj_id, target_obj_id, data):
        if self.new:
            q = self._find_target_obj_query()
            anamnesis_exists = db.session.query(q.exists()).scalar()
            if anamnesis_exists:
                raise ApiException(
                    ALREADY_PRESENT_ERROR,
                    u'Уже существует анамнез матери для карты с id = {0}'.format(self.parent_obj_id)
                )

    def get_target_nf_msg(self):
        return u'Не найден анамнез матери для карты с id = {0}'.format(self.parent_obj_id)

    def convert_and_format(self, data):
        res = {}
        res.update({
            'education': self.to_rb(data.get('education')),
            'work_group': self.to_rb(data.get('work_group')),
            'professional_properties': self.to_rb(data.get('professional_properties')),
            'family_income': self.to_rb(data.get('family_income')),
            'menstruation_start_age': data.get('menstruation_start_age'),
            'menstruation_duration': data.get('menstruation_duration'),
            'menstruation_period': data.get('menstruation_period'),
            'menstruation_disorders': safe_bool(data.get('menstrual_disorder')),
            'sex_life_start_age': safe_int(data.get('sex_life_age')),
            'fertilization_type': self.to_rb(data.get('fertilization_type')),
            'intrauterine': safe_bool(data.get('intrauterine_operation')),
            'multifetation': safe_bool(data.get('multiple_fetation')),

            'smoking': safe_bool(data.get('smoking')),
            'alcohol': safe_bool(data.get('alcohol')),
            'toxic': safe_bool(data.get('toxic')),
            'drugs': safe_bool(data.get('drugs')),
            'contraception': map(self.to_rb, data.get('contraception', [])),
            'hereditary': map(self.to_rb, data.get('hereditary', [])),

            'finished_diseases_text': data.get('finished_diseases'),
            'current_diseases': map(self.to_mkb_rb, data.get('current_diseases', [])),

            'menstruation_last_date': safe_date(data.get('last_period_date')),
            'preeclampsia': safe_bool(data.get('preeclampsia_mother_sister')),
            'marital_status': self.to_rb(data.get('marital_status'))
        })
        if 'infertility' in data:
            res.update({
                'infertility': safe_bool(data['infertility']['infertility_occurence']),
                'infertility_type': self.to_rb(data['infertility']['infertility_type']),
                'infertility_period': safe_int(data['infertility']['infetrility_duration']),
                'infertility_treatment': map(self.to_rb, data['infertility']['infertility_treatment']),
                'infertility_cause': map(self.to_rb, data['infertility']['infertility_causes']),
            })
        return res

    @wrap_simplify
    def as_json(self):
        an_props = self.target_obj.propsByCode
        return {
            'education': self.from_rb(an_props['education'].value),
            'work_group': self.from_rb(an_props['work_group'].value),
            'professional_properties': self.from_rb(an_props['professional_properties'].value),
            'family_income': self.from_rb(an_props['family_income'].value),
            'menstruation_start_age': an_props['menstruation_start_age'].value,
            'menstruation_duration': an_props['menstruation_duration'].value,
            'menstruation_period': an_props['menstruation_period'].value,
            'menstrual_disorder': an_props['menstruation_disorders'].value,
            'sex_life_age': an_props['sex_life_start_age'].value,
            'fertilization_type': self.from_rb(an_props['fertilization_type'].value),
            'intrauterine_operation': an_props['intrauterine'].value,
            'multiple_fetation': an_props['multifetation'].value,

            'intertility': self._represent_intertility(),

            'smoking': an_props['smoking'].value,
            'alcohol': an_props['alcohol'].value,
            'toxic': an_props['toxic'].value,
            'drugs': an_props['drugs'].value,
            'contraception': map(self.from_rb, an_props['contraception'].value),
            'hereditary': map(self.from_rb, an_props['hereditary'].value),

            'finished_diseases': an_props['finished_diseases_text'].value,
            'current_diseases': map(self.from_mkb_rb, an_props['current_diseases'].value),

            'last_period_date': an_props['menstruation_last_date'].value,
            'preeclampsia_mother_sister': an_props['preeclampsia'].value,
            'marital_status': self.from_rb(an_props['marital_status'].value)
        }

    @none_default
    def _represent_intertility(self):
        an_props = self.target_obj.propsByCode
        return {
            'infertility_occurence': an_props['infertility'].value,
            'infertility_type': self.from_rb(an_props['infertility_type'].value),
            'infetrility_duration': an_props['infertility_period'].value,
            'infertility_treatment': map(self.from_rb, an_props['infertility_treatment'].value),
            'infertility_causes': map(self.from_rb, an_props['infertility_cause'].value)
        }


class AnamnesisFatherXForm(AnamnesisFatherSchema, AnamnesisXForm):
    """
    Класс-преобразователь для документа анамнеза отца
    """
    target_obj_class = Action
    parent_obj_class = Event
    target_id_required = False
    flat_code = risar_father_anamnesis

    def check_duplicate(self, parent_obj_id, target_obj_id, data):
        if self.new:
            q = self._find_target_obj_query()
            anamnesis_exists = db.session.query(q.exists()).scalar()
            if anamnesis_exists:
                raise ApiException(
                    ALREADY_PRESENT_ERROR,
                    u'Уже существует анамнез отца для карты с id = {0}'.format(self.parent_obj_id)
                )

    def get_target_nf_msg(self):
        return u'Не найден анамнез отца для карты с id = {0}'.format(self.parent_obj_id)

    def convert_and_format(self, data):
        res = {}
        res.update({
            'name': data.get('FIO'),
            'age': safe_int(data.get('age')),
            'education': self.to_rb(data.get('education')),
            'work_group': self.to_rb(data.get('work_group')),
            'professional_properties': self.to_rb(data.get('professional_properties')),
            'phone': data.get('telephone_number'),
            'fluorography': data.get('fluorography'),
            'HIV': safe_bool(data.get('hiv')),
            'blood_type': self.to_blood_type_rb(data.get('blood_type')),

            'smoking': safe_bool(data.get('smoking')),
            'alcohol': safe_bool(data.get('alcohol')),
            'toxic': safe_bool(data.get('toxic')),
            'drugs': safe_bool(data.get('drugs')),
            'hereditary': map(self.to_rb, data.get('hereditary', [])),

            'finished_diseases_text': data.get('finished_diseases'),
            'current_diseases_text': data.get('current_diseases'),
        })
        if 'infertility' in data:
            res.update({
                'infertility': safe_bool(data['infertility']['infertility_occurence']),
                'infertility_type': self.to_rb(data['infertility']['infertility_type']),
                'infertility_period': safe_int(data['infertility']['infetrility_duration']),
                'infertility_treatment': map(self.to_rb, data['infertility']['infertility_treatment']),
                'infertility_cause': map(self.to_rb, data['infertility']['infertility_causes']),
            })
        return res

    @wrap_simplify
    def as_json(self):
        an_props = self.target_obj.propsByCode
        return {
            'FIO': an_props['name'].value,
            'age': an_props['age'].value,
            'education': self.from_rb(an_props['education'].value),
            'work_group': self.from_rb(an_props['work_group'].value),
            'professional_properties': self.from_rb(an_props['professional_properties'].value),
            'telephone_number': an_props['phone'].value,
            'fluorography': an_props['fluorography'].value,
            'hiv': an_props['HIV'].value,
            'blood_type': self.from_blood_type_rb(an_props['blood_type'].value),

            'intertility': self._represent_intertility(),

            'smoking': an_props['smoking'].value,
            'alcohol': an_props['alcohol'].value,
            'toxic': an_props['toxic'].value,
            'drugs': an_props['drugs'].value,
            'hereditary': map(self.from_rb, an_props['hereditary'].value),

            'finished_diseases': an_props['finished_diseases_text'].value,
            'current_diseases': an_props['current_diseases_text'].value
        }

    @none_default
    def _represent_intertility(self):
        an_props = self.target_obj.propsByCode
        return {
            'infertility_occurence': an_props['infertility'].value,
            'infertility_type': self.from_rb(an_props['infertility_type'].value),
            'infetrility_duration': an_props['infertility_period'].value,
            'infertility_treatment': map(self.from_rb, an_props['infertility_treatment'].value),
            'infertility_causes': map(self.from_rb, an_props['infertility_cause'].value)
        }


class AnamnesisPrevPregXForm(AnamnesisPrevPregSchema, AnamnesisXForm):
    """
    Класс-преобразователь для анамнеза предыдущих беременностей
    """
    target_obj_class = Action
    parent_obj_class = Event
    flat_code = risar_anamnesis_pregnancy

    def _find_target_obj_query(self):
        return Action.query.join(ActionType).filter(
            Action.deleted == 0,
            Action.id == self.target_obj_id,
            ActionType.flatCode == self.flat_code
        )

    def get_target_nf_msg(self):
        return u'Не найден анамнез предыдущей беременности с id = {0}'.format(self.target_obj_id)

    def check_duplicate(self, parent_obj_id, target_obj_id, data):
        pass

    def convert_and_format(self, data):
        res = {}
        res.update({
            'year': safe_int(data.get('pregnancy_year')),
            'pregnancyResult': self.to_rb(data.get('pregnancy_result')),
            'pregnancy_week': safe_int(data.get('gestational_age')),
            'preeclampsia': safe_bool(data.get('preeclampsia')),
            'after_birth_complications': map(self.to_mkb_rb, data.get('after_birth_complications', [])),
            'maternity_aid': map(self.to_rb, data.get('assistance_and_operations', [])),
            'pregnancy_pathology': map(self.to_mkb_rb, data.get('pregnancy_pathologies', [])),
            'delivery_pathology': map(self.to_mkb_rb, data.get('birth_pathologies', [])),
            'note': data.get('features'),
        })
        newborn_inspections = []
        for child_data in data.get('child_information', []):
            newborn_inspections.append({
                'alive': safe_bool(child_data.get('is_alive')),
                'weight': safe_int(child_data.get('weight')),
                'death_reason': child_data.get('death_cause'),
                'died_at': self.to_rb(child_data.get('death_at')),
                'abnormal_development': safe_bool(child_data.get('abnormal_development')),
                'neurological_disorders': safe_bool(child_data.get('neurological_disorders'))
            })
        res.update(newborn_inspections=newborn_inspections)
        return res

    def update_target_obj(self, data):
        data = self.convert_and_format(data)

        action_id = self.target_obj_id
        event = self.parent_obj = self.find_event(self.parent_obj_id)
        anamnesis = self.target_obj = get_action_by_id(
            action_id, event, self.flat_code, True
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

        newborn_inspections = data.get('newborn_inspections', [])
        new_children, deleted_children = create_or_update_prev_children(anamnesis, newborn_inspections)

        self._changed.append(self.target_obj)
        self._changed.extend(new_children)
        self._deleted.extend(deleted_children)

    def delete_target_obj(self):
        self.parent_obj = self.find_event(self.parent_obj_id)
        self.target_obj_class.query.join(ActionType, Event).filter(
            self.parent_obj_class.id == self.parent_obj_id,
            ActionType.flatCode == self.flat_code,
            self.target_obj_class.id == self.target_obj_id,
            Action.event_id == Event.id
        ).update({self.target_obj_class.deleted: 1})

    @wrap_simplify
    def as_json(self):
        an_props = self.target_obj.propsByCode
        return {
            'prevpregnancy_id': str(self.target_obj.id),
            'pregnancy_result': self.from_rb(an_props['pregnancyResult'].value),
            'gestational_age': an_props['pregnancy_week'].value,
            'preeclampsia': an_props['preeclampsia'].value,
            'after_birth_complications': map(self.from_mkb_rb, an_props['after_birth_complications'].value),
            'assistance_and_operations': map(self.from_rb, an_props['maternity_aid'].value),
            'pregnancy_pathologies': map(self.from_mkb_rb, an_props['pregnancy_pathology'].value),
            'birth_pathologies': map(self.from_mkb_rb, an_props['delivery_pathology'].value),
            'features': an_props['note'].value,
            'child_information': self._represent_children(),
        }

    @none_default
    def _represent_children(self):
        prev_children = get_previous_children(self.target_obj.id)
        return [
            {
                'is_alive': child.alive,
                'weight': child.weight,
                'death_cause': child.death_reason,
                'death_at': child.died_at,
                'abnormal_development': child.abnormal_development,
                'neurological_disorders': child.neurological_disorders,
            }
            for child in prev_children
        ]
