#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from hippocrates.blueprints.risar.views.api.integration.errands.schemas import \
    ErrandSchema, ErrandListSchema
from hippocrates.blueprints.risar.views.api.integration.xform import XForm, wrap_simplify
from hippocrates.blueprints.risar.lib.represent import make_file_url
from nemesis.lib.utils import safe_date
from nemesis.models.event import Event
from nemesis.models.risar import Errand, rbErrandStatus


class ErrandXForm(ErrandSchema, XForm):
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
        target_obj_query = self._find_target_obj_query()
        self.target_obj = target_obj_query.first()
        self.target_obj.execDate = safe_date(data.get('execution_date'))
        self.target_obj.result = data.get('execution_comment')
        status_code = data.get('status')
        self._check_rb_value('rbErrandStatus', status_code)
        new_status = rbErrandStatus.query.filter(rbErrandStatus.code == status_code).first()
        self.target_obj.status = new_status

    def delete_target_obj_data(self):
        self._find_target_obj_query().update({
            'execDate': None,
            'result': None,
            'status_id': None
        })

    @wrap_simplify
    def as_json(self):
        return {
            'errands_id': self.target_obj.id,
            'communication': self.target_obj.communications,
            'status': self.or_undefined(self.from_rb(self.target_obj.status)),
            'execution_date': self.or_undefined(safe_date(self.target_obj.execDate)),
            'execution_comment': self.or_undefined(self.target_obj.result),
        }


class ErrandListXForm(ErrandListSchema, XForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Errand
    target_id_required = False

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

    @wrap_simplify
    def as_json(self):
        target_obj_query = self._find_target_obj_query()
        target_obj_query = target_obj_query.filter(
            self.target_obj_class.execDate.is_(None),
        )
        res = []
        for errand in target_obj_query.all():
            res.append({
                'errands_id': errand.id,
                'hospital': self.from_org_rb(errand.setPerson and errand.setPerson.organisation),
                'doctor': self.from_person_rb(errand.setPerson),
                'date': safe_date(errand.plannedExecDate),
                'comment': errand.text,
                'execution_hospital': self.from_org_rb(errand.execPerson and errand.execPerson.organisation),
                'execution_doctor': self.from_person_rb(errand.execPerson),
                'status': self.from_rb(errand.status),
                'communication': "\\n".join(errand.communications.split('\n')),
                'attached_files': [
                    self._represent_attached_file(attach)
                    for attach in errand.attach_files
                ]
            })
        return res

    def _represent_attached_file(self, efa):
        filemeta = efa.file_meta
        return {
            'id': str(efa.id),
            "name": filemeta.name,
            "url": make_file_url(filemeta),
            "comment": filemeta.note,
            "doctor_code": self.from_person_rb(efa.set_person),
            "hospital_code": self.from_org_rb(efa.set_person and efa.set_person.organisation),
            "attach_date": safe_date(efa.attachDate),
            "mimetype": filemeta.mimetype
        }
