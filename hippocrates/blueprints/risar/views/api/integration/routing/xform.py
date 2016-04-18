#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 22.03.2016

"""
from blueprints.risar.lib.represent import get_lpu_attached
from blueprints.risar.views.api.integration.routing.schemas import \
    RoutingSchema
from blueprints.risar.views.api.integration.xform import XForm
from nemesis.models.event import Event, EventType


class RoutingXForm(RoutingSchema, XForm):
    """
    Класс-преобразователь
    """
    target_obj_class = Event
    parent_id_required = False

    def check_duplicate(self, data):
        pass

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(EventType).filter(
            self.target_obj_class.id == self.target_obj_id,
            self.target_obj_class.deleted == 0,
        )
        return res

    def as_json(self):
        self.find_target_obj(self.target_obj_id)
        event = self.target_obj
        client = event.client
        lpu_attached = get_lpu_attached(client.attachments)
        # todo: сформировать список ЛПУ
        hospital_planned_list = []
        hospital_emergency_list = []

        res = {
            'hospital_planned': lpu_attached.plan_lpu.org.code,
            'hospital_emergency': lpu_attached.extra_lpu.org.code,
            'hospital_planned_list': hospital_planned_list,
            'hospital_emergency_list': hospital_emergency_list,
        }
        return res
