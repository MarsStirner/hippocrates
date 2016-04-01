# -*- coding: utf-8 -*-
from flask import request

from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import public_endpoint
from nemesis.systemwide import db
from .....app import module

from ..logformat import hook
from .xform import CardXForm


@module.route('/api/integration/<int:api_version>/card/schema.json', methods=["GET"])
@api_method(hook=hook)
@public_endpoint
def api_card_schema(api_version):
    try:
        return CardXForm.schema[api_version]
    except IndexError:
        raise ApiException(
            404,
            u'Api version {0} is not supported. Maximum is {0}'.format(api_version, len(CardXForm.schema) - 1)
        )


@module.route('/api/integration/<int:api_version>/card/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<int:card_id>', methods=['PUT'])
@api_method(hook=hook)
def api_card_save(api_version, card_id=None):
    data = request.get_json()
    xform = CardXForm()
    xform.set_version(api_version)
    xform.validate(data)
    xform.find_card(card_id, data)
    xform.update_card(data)
    db.session.add(xform.event)
    db.session.commit()

    xform.update_card_attrs()
    db.session.add(xform.ca_action)
    db.session.commit()
    return xform.as_json()


@module.route('/api/integration/<int:api_version>/card/<card_id>', methods=['DELETE'])
@api_method(hook=hook)
def api_card_delete(api_version, card_id):
    xform = CardXForm()
    xform.set_version(api_version)
    xform.find_card(card_id)
    xform.delete_card()
    db.session.add(xform.event)
    db.session.commit()

    return xform.as_json()