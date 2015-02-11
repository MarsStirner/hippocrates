# -*- coding: utf-8 -*-
from ..app import module
from application.lib.utils import api_method
from blueprints.risar_config.views.represent import represent_organisation
from application.models.exists import Organisation

__author__ = 'viruzzz-kun'


@module.route('/api/routing.json')
@api_method
def api_routing():
    return map(represent_organisation, Organisation.query.filter(Organisation.isHospital == 1))