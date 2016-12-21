#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.epicrisis.schemas import \
    EpicrisisSchema
from hippocrates.blueprints.risar.views.api.integration.xform import XForm
from nemesis.lib.utils import safe_date
from nemesis.models.event import Event


class EpicrisisXForm(EpicrisisSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Event
    parent_id_required = False

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.filter(
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0,
        )
        return res

    def check_duplicate(self, data):
        pass

    def update_target_obj(self, data):
        exec_person = self.find_doctor(data.get('hospital_doctor'), data.get('hospital'))
        manager = self.find_doctor(data.get('hospital_chief_doctor'), data.get('hospital'))
        self._find_target_obj_query().update({
            'execPerson_id': exec_person.id,
            'execDate': safe_date(data.get('date_close')),
            'manager_id': manager.id,
        })

    def delete_target_obj(self):
        self._find_target_obj_query().update({
            'execDate': None,
            'manager_id': None,
        })

    def as_json(self):
        self.find_target_obj(self.target_obj_id)
        res = {
            'hospital': self.target_obj.execPerson.organisation and self.target_obj.execPerson.organisation.regionalCode or '',
            'hospital_doctor': self.target_obj.execPerson.regionalCode,
            'hospital_chief_doctor': self.target_obj.manager and self.target_obj.manager.regionalCode or '',
            'date_close': self.safe_represent_val(self.target_obj.execDate),
        }
        return res
