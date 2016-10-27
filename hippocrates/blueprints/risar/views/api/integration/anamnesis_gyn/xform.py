# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify, ALREADY_PRESENT_ERROR
from .schemas import AnamnesisGynSchema

from hippocrates.blueprints.risar.risar_config import risar_gyn_general_anamnesis_flat_code
from hippocrates.blueprints.risar.lib.utils import get_action

from nemesis.systemwide import db
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_bool_none
from nemesis.models.event import Event
from nemesis.models.actions import Action, ActionType


logger = logging.getLogger('simple')


class AnamnesisGynXForm(AnamnesisGynSchema, XForm):
    """
    Класс-преобразователь для документа анамнеза небеременной
    """
    target_obj_class = Action
    parent_obj_class = Event
    target_id_required = False
    flat_code = risar_gyn_general_anamnesis_flat_code

    def check_duplicate(self, data):
        q = self._find_target_obj_query()
        anamnesis_exists = db.session.query(q.exists()).scalar()
        if anamnesis_exists:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует анамнез для карты с id = {0}'.format(self.parent_obj_id)
            )

    def get_target_nf_msg(self):
        return u'Не найден анамнез для карты с id = {0}'.format(self.parent_obj_id)

    def _find_target_obj_query(self):
        return Action.query.join(ActionType).filter(
            Action.deleted == 0,
            Action.event_id == self.parent_obj_id,
            ActionType.flatCode == self.flat_code
        )

    def get_parent_nf_msg(self):
        return u'Не найдена карта с id = {0}'.format(self.parent_obj_id)

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
        action_ids = [r[0] for r in db.session.query(Action.id).join(ActionType, Event).filter(
            Event.id == self.parent_obj_id,
            ActionType.flatCode == self.flat_code,
        ).all()]
        if action_ids:
            self.target_obj_class.query.filter(
                self.target_obj_class.id.in_(action_ids)
            ).update({self.target_obj_class.deleted: 1}, synchronize_session=False)

    def convert_and_format(self, data):
        res = {}
        res.update({
            'age': data.get('age'),
            'duration': data.get('duration'),
            'period_duration': data.get('period_duration'),
            'disorder': safe_bool_none(data.get('disorder')),
            'menstrual_character': map(self.to_rb, data.get('menstrual_character', [])),
            'intermenstrual_spotting': data.get('intermenstrual_spotting'),
            'menstrual_pain': data.get('menstrual_pain'),
            'menopause': safe_bool_none(data.get('menopause')),
            'menopause_age': data.get('menopause_age'),
            'sex_life_age': data.get('sex_life_age'),
            'intercourse_partner_number': data.get('intercourse_partner_number'),
            'marital_status': self.to_rb(data.get('marital_status')),
            'std': map(self.to_rb, data.get('std', [])),
            'gynecopathy': map(self.to_rb, data.get('gynecopathy', [])),
            'hepatitis': data.get('hepatitis'),
            'tuberculosis': data.get('tuberculosis'),
            'somatic_disease': data.get('somatic_disease'),
            'hereditary': map(self.to_rb, data.get('hereditary', [])),
            'gyn_operation': data.get('gyn_operation'),
            'infertility': safe_bool_none(data.get('infertility')),
            'infertility_kind': self.to_rb(data.get('infertility_kind')),
            'infertility_duration': data.get('infertility_duration'),
            'infertility_etiology': map(self.to_rb, data.get('infertility_etiology', [])),
            'infertility_treatment': map(self.to_rb, data.get('infertility_treatment', [])),
            'traumas': data.get('traumas'),
            'operations': data.get('operations'),
            'alcohol': safe_bool_none(data.get('alcohol')),
            'smoking': safe_bool_none(data.get('smoking')),
            'drugs': safe_bool_none(data.get('drugs')),
            'toxic': safe_bool_none(data.get('toxic')),
            'work_group': self.to_rb(data.get('work_group')),
            'professional_properties': self.to_rb(data.get('professional_properties')),
            'additional_info': safe_bool_none(data.get('additional_info')),
            'epidemic': safe_bool_none(data.get('epidemic')),
        })
        return res

    @wrap_simplify
    def as_json(self):
        an_props = self.target_obj.propsByCode
        return {
            'age': self.or_undefined(an_props['age'].value),
            'duration': self.or_undefined(an_props['duration'].value),
            'period_duration': self.or_undefined(an_props['period_duration'].value),
            'disorder': self.or_undefined(an_props['disorder'].value),
            'menstrual_character': self.or_undefined(map(self.from_rb, an_props['menstrual_character'].value)),
            'intermenstrual_spotting': self.or_undefined(an_props['intermenstrual_spotting'].value),
            'menstrual_pain': self.or_undefined(an_props['menstrual_pain'].value),
            'menopause': self.or_undefined(an_props['menopause'].value),
            'menopause_age': self.or_undefined(an_props['menopause_age'].value),
            'sex_life_age': self.or_undefined(an_props['sex_life_age'].value),
            'intercourse_partner_number': self.or_undefined(an_props['intercourse_partner_number'].value),
            'marital_status': self.or_undefined(self.from_rb(an_props['marital_status'].value)),
            'std': self.or_undefined(map(self.from_rb, an_props['std'].value)),
            'gynecopathy': self.or_undefined(map(self.from_rb, an_props['gynecopathy'].value)),
            'hepatitis': self.or_undefined(an_props['hepatitis'].value),
            'tuberculosis': self.or_undefined(an_props['tuberculosis'].value),
            'somatic_disease': self.or_undefined(an_props['somatic_disease'].value),
            'hereditary': self.or_undefined(map(self.from_rb, an_props['hereditary'].value)),
            'gyn_operation': self.or_undefined(an_props['gyn_operation'].value),
            'infertility': self.or_undefined(an_props['infertility'].value),
            'infertility_kind': self.or_undefined(self.from_rb(an_props['infertility_kind'].value)),
            'infertility_duration': self.or_undefined(an_props['infertility_duration'].value),
            'infertility_etiology': self.or_undefined(map(self.from_rb, an_props['infertility_etiology'].value)),
            'infertility_treatment': self.or_undefined(map(self.from_rb, an_props['infertility_treatment'].value)),
            'traumas': self.or_undefined(an_props['traumas'].value),
            'operations': self.or_undefined(an_props['operations'].value),
            'alcohol': self.or_undefined(an_props['alcohol'].value),
            'smoking': self.or_undefined(an_props['smoking'].value),
            'drugs': self.or_undefined(an_props['drugs'].value),
            'toxic': self.or_undefined(an_props['toxic'].value),
            'work_group': self.or_undefined(self.from_rb(an_props['work_group'].value)),
            'professional_properties': self.or_undefined(self.from_rb(an_props['professional_properties'].value)),
            'additional_info': self.or_undefined(an_props['additional_info'].value),
            'epidemic': self.or_undefined(an_props['epidemic'].value),
        }
