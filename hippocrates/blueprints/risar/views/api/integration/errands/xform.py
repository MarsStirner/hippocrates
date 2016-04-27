#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
import logging
from blueprints.risar.views.api.integration.errands.schemas import \
    ErrandsSchema
from blueprints.risar.views.api.integration.xform import XForm
from nemesis.lib.utils import safe_date
from nemesis.models.event import Event
from nemesis.models.risar import Errand

logger = logging.getLogger('simple')


class ErrandsXForm(ErrandsSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Errand

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def check_duplicate(self, data):
        pass

    def update_target_obj(self, data):
        self._find_target_obj_query().update({
            'execDate': safe_date(data.get('execution_date')),
            'result': data.get('execution_comment'),
        })

    def delete_target_obj(self):
        self._find_target_obj_query().update({
            'execDate': None,
            'result': None,
        })

    def as_json(self):
        target_obj_query = self._find_target_obj_query()
        target_obj_query = target_obj_query.filter(
            self.target_obj_class.execDate.is_(None),
        )
        res = []
        for errand in target_obj_query.all():
            res.append({
                'errands_id': errand.id,
                'hospital': errand.setPerson.organisation and errand.setPerson.organisation.TFOMSCode or '',
                'doctor': errand.setPerson.regionalCode,
                'date': self.safe_represent_val(errand.plannedExecDate),
                'comment': errand.text or '',
                'execution_hospital': errand.execPerson.organisation and errand.execPerson.organisation.TFOMSCode or '',
                'execution_doctor': errand.execPerson.regionalCode,
                # 'execution_date': self.safe_represent_val(errand.execDate),
                # 'execution_comment': errand.result or '',
            })
        return res
