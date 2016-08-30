# -*- coding: utf-8 -*-

import logging

from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import api_method
from .....app import module

from ..logformat import hook
from .xform import ScheduleTicketsXForm


logger = logging.getLogger('simple')


@module.route('/api/integration/<int:api_version>/card/schedule_tickets.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_schedule_tickets_schema(api_version):
    return ScheduleTicketsXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<card_id>/schedule_tickets/')
@api_method(hook=hook)
def api_schedule_tickets_get(api_version, card_id):
    xform = ScheduleTicketsXForm(api_version)
    xform.check_params(None, card_id)
    return xform.as_json()
