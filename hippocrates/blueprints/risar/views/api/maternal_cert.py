# -*- encoding: utf-8 -*-
from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.mat_cert import save_maternal_cert
from nemesis.lib.apiutils import api_method
from nemesis.systemwide import db
from nemesis.models.risar import MaternalCertificate


@module.route('/api/0/maternal_cert/<int:cert_id>', methods=['POST'])
@module.route('/api/0/maternal_cert/', methods=['POST'])
@api_method
def api_0_maternal_cert_save(cert_id=None):
    json_data = request.get_json()
    cert = save_maternal_cert(cert_id, json_data)
    db.session.add(cert)
    db.session.commit()
    return cert


@module.route('/api/0/maternal_cert_for_event/<int:event_id>', methods=['GET'])
@api_method
def api_0_maternal_cert_for_event(event_id):
    cert = MaternalCertificate.query.filter(
        MaternalCertificate.event_id == event_id,
        MaternalCertificate.deleted == 0
    ).order_by(
        MaternalCertificate.id.desc()
    ).first()
    return cert
