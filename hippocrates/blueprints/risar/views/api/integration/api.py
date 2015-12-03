# -*- coding: utf-8 -*-
from blueprints.risar.views.api.integration.xform import ClientXForm
from nemesis.lib.apiutils import api_method
from nemesis.models.client import Client
from ....app import module

__author__ = 'viruzzz-kun'


@module.route('/api/0/integration/client/<int:client_id>', methods=['GET'])
@api_method
def api_0_client_get(client_id):
    return ClientXForm(Client.query.get(client_id))
