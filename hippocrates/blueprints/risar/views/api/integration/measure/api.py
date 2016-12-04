# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from .....app import module

from ..logformat import hook
from .xform import MeasureListXForm, MeasureXForm


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


@module.route('/api/integration/<int:api_version>/card/<card_id>/measures/<int:measure_id>', methods=["GET"])
@api_method(hook=hook)
def api_measure_get(api_version, card_id, measure_id=None):
    xform = MeasureXForm(api_version, False)
    xform.check_params(measure_id, card_id)
    xform.load_data()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<card_id>/measures/', methods=["POST"])
@module.route('/api/integration/<int:api_version>/card/<card_id>/measures/<int:measure_id>', methods=["PUT"])
@api_method(hook=hook)
def api_measure_save(api_version, card_id, measure_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = MeasureXForm(api_version, create)
    xform.validate(data)
    xform.check_params(measure_id, card_id, data)
    # todo: обновление не реализовано
    if create:
        xform.update_target_obj(data)
        xform.store()
    else:
        xform.load_data()
    return xform.as_json()
