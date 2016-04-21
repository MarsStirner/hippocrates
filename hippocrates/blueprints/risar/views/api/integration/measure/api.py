# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from .....app import module

from ..logformat import hook
from .xform import MeasureListXForm


@module.route('/api/integration/<int:api_version>/measures/list/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_measure_list_schema(api_version):
    return MeasureListXForm.get_schema(api_version)


@module.route('/api/integration/<int:api_version>/card/<card_id>/measures/list/', methods=["GET"])
@api_method(hook=hook)
def api_measure_list_get(api_version, card_id):
    xform = MeasureListXForm(api_version)
    args = request.args.to_dict()
    xform.check_params(None, card_id)
    xform.load_data(args)
    return xform.as_json()
