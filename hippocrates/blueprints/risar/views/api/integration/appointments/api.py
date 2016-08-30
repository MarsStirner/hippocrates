# -*- coding: utf-8 -*-

from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import public_endpoint
from .....app import module

from ..logformat import hook
from .xform import AppointmentListXForm, AppointmentXForm


@module.route('/api/integration/<int:api_version>/appointments/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_appointment_list_schema(api_version):
    return AppointmentListXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<card_id>/appointments/', methods=["GET"])
@api_method(hook=hook)
def api_appointment_list_get(api_version, card_id):
    xform = AppointmentListXForm(api_version)
    xform.check_params(None, card_id)
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/appointment/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_appointment_schema(api_version):
    return AppointmentXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<card_id>/appointments/<int:appointment_id>', methods=["GET"])
@api_method(hook=hook)
def api_appointment_get(api_version, card_id, appointment_id):
    xform = AppointmentXForm(api_version)
    xform.check_params(appointment_id, card_id)
    xform.find_target_obj(appointment_id)
    return xform.as_json()
