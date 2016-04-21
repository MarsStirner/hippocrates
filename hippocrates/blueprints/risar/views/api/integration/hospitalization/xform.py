#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from blueprints.risar.risar_config import general_hospitalizations
from blueprints.risar.views.api.integration.hospitalization.schemas import \
    HospitalizationSchema
from blueprints.risar.views.api.integration.xform import ExternalXForm, \
    NOT_FOUND_ERROR
from nemesis.lib.utils import safe_int, safe_date
from nemesis.models.actions import Action, ActionType
from nemesis.models.event import Event
from nemesis.models.expert_protocol import EventMeasure
from nemesis.lib.apiutils import ApiException
from nemesis.systemwide import db

logger = logging.getLogger('simple')


class HospitalizationXForm(HospitalizationSchema, ExternalXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == general_hospitalizations,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        self.em = self.get_event_measure(data['measure_id'])
        self.person = self.find_doctor(data.get('doctor'), data.get('doctor'))

        if self.new:
            self.create_action()
        else:
            self.find_target_obj(self.target_obj_id)

        properties_data = self.get_properties_data(data)
        self.set_properties(properties_data)
        self.save_external_data()

    def get_event_measure(self, event_measure_id):
        em = EventMeasure.query.get(event_measure_id)
        if not em:
            raise ApiException(NOT_FOUND_ERROR,
                               u'Не найдено EM с id = '.format(event_measure_id))
        return em

    def create_action(self):
        # by blueprints.risar.views.api.measure.api_0_event_measure_result_save

        em_ctrl = EventMeasureController()
        em_result = em_ctrl.get_new_em_result(self.em)
        self.em.result_action = em_result
        em_ctrl.make_assigned(self.em)
        db.session.add_all((self.em, em_result))

        self.target_obj = em_result

    def get_properties_data(self, data):
        return {
            'ReceiptDate': safe_date(data.get('date_in')),
            'IssueDate': safe_date(data.get('date_out')),
            'Doctor': self.person,
            'PregnancyDuration': safe_int(data.get('pregnancy_week')),
            'DirectionDiagnosis': self.to_mkb_rb(data.get('diagnosis_in')),
            'FinalDiagnosis': self.to_mkb_rb(data.get('diagnosis_out')),
        }

    def set_properties(self, data):
        for code, value in data.iteritems():
            if code in self.target_obj.propsByCode:
                try:
                    prop = self.target_obj.propsByCode[code]
                    self.check_prop_value(prop, value)
                    prop.value = value
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise

    def delete_target_obj(self):
        #  Евгений: Пока диагнозы можешь не закрывать и не удалять.
        # self.close_diags()

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0
        ).update({'deleted': 1})

    def as_json(self):
        an_props = self.target_obj.propsByCode
        res = {
            'external_id': self.external_id,
            'hospitalization_id': self.target_obj_id,
            'measure_id': self.em.id,
            'date_in': an_props['ReceiptDate'].value,
            'date_out': an_props['IssueDate'].value,
            'hospital': self.person.organisation and self.person.organisation.TFOMSCode or '',
            'doctor': self.person.regionalCode,
            'pregnancy_week': an_props['PregnancyDuration'].value,
            'diagnosis_in': an_props['DirectionDiagnosis'].value,
            'diagnosis_out': an_props['FinalDiagnosis'].value,
        }
        return res
