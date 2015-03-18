# -*- coding: utf-8 -*-
from flask import request
import itertools
from ..app import module
from nemesis.lib.utils import api_method
from nemesis.systemwide import db
from blueprints.risar_config.views.represent import represent_organisation
from nemesis.models.exists import Organisation, MKB

__author__ = 'viruzzz-kun'


@module.route('/api/routing.json', methods=['GET'])
@api_method
def api_routing_get():
    return map(represent_organisation, Organisation.query.filter(Organisation.isHospital == 1))


@module.route('/api/routing.json', methods=['POST'])
@api_method
def api_routing_post():
    data = request.get_json()
    mkb_ids = set(
        mkb['id']
        for mkb in itertools.chain.from_iterable(
            org['diagnoses']
            for org in data
        )
    )
    mkb_dict = dict(
        (mkb.id, mkb)
        for mkb in MKB.query.filter(MKB.id.in_(mkb_ids))
    )
    org_dict = dict(
        (org.id, org)
        for org in Organisation.query.filter(Organisation.isHospital == 1)
    )
    for org in data:
        org_dict[org['id']].mkbs = [
            mkb_dict[mkb['id']]
            for mkb in org['diagnoses']
            if 'id' in mkb
        ]
    db.session.commit()
    return map(represent_organisation, Organisation.query.filter(Organisation.isHospital == 1))