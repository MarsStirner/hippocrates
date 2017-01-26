# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, ALREADY_PRESENT_ERROR
from .schemas import RefbookSchema

from nemesis.models import expert_protocol, exists, refbooks, risar, person
from nemesis.systemwide import db
from nemesis.lib.utils import safe_bool, safe_int
from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import get_new_uuid


logger = logging.getLogger('simple')


class RefbookXForm(RefbookSchema, XForm):
    """
    Класс-преобразователь
    """
    target_id_required = True
    parent_id_required = False
    refbook_code = None
    item_code = None

    def check_duplicate(self, data):
        code = data['code']
        q = self._find_target_obj_query()
        rb_exists = db.session.query(q.exists()).scalar()
        if rb_exists:
            raise ApiException(
                ALREADY_PRESENT_ERROR,
                u'Уже существует {0} c кодом {1}'.format(self.refbook_code, code)
            )

    def check_external_id(self, data):
        pass

    def _find_target_obj_query(self):
        query = self.target_obj_class.query.filter(
            self.target_obj_class.regionalCode == self.item_code
        )
        if hasattr(self.target_obj_class, 'deleted'):
            query = query.filter(
                self.target_obj_class.deleted == 0,
            )
        return query

    def set_target_class(self, refbook_code):
        self.refbook_code = refbook_code
        modules = {
            'rbMeasureStatus': expert_protocol,
            'rbResult': exists,
            'rbDiseaseCharacter': exists,
            'rbTraumaType': exists,
            'rbAcheResult': exists,
            'rbFinance': refbooks,
            'rbDispanser': exists,
            'rbConditionMedHelp': risar,
            'rbProfMedHelp': risar,
            'rbSpeciality': person,
            'rbPost': person,
        }
        module = modules[refbook_code]
        model = getattr(module, refbook_code)
        self.target_obj_class = model

    def find_refbook(self):
        q = self._find_target_obj_query()
        res = q.first()
        return res

    def init_and_check_params(self, refbook_code, item_code=None, data=None):
        self.item_code = item_code
        self.set_target_class(refbook_code)
        super(RefbookXForm, self).check_params(item_code and 1, data=data)
        if not self.new:
            self.target_obj = self.find_refbook()

    def update_target_obj(self, data):
        if self.new:
            self.target_obj = self.target_obj_class()
            self._changed.append(self.target_obj)
            self.target_obj.code = data.get('code') or ''
            self.target_obj.regionalCode = data.get('code') or ''

        self.target_obj.name = data.get('value') or ''

    def as_json(self):
        if self.target_obj:
            return self.rb_represent(self.target_obj)
        else:
            res = []
            for rb in self._find_target_obj_query():
                res.append(self.rb_represent(rb))
            return res

    def rb_represent(self, target_obj):
        return {
            'code': target_obj.regionalCode,
            'value': target_obj.name,
        }

    def delete_target_obj(self):
        if hasattr(self.target_obj, 'deleted'):
            self.target_obj.deleted = 1
            self._changed.append(self.target_obj)
        else:
            self._deleted.append(self.target_obj)
