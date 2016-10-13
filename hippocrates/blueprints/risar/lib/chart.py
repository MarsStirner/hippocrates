# coding: utf-8
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy
from nemesis.models.event import Event, EventType
from nemesis.models.risar import MaternalCertificate
from nemesis.models.exists import rbRequestType
from nemesis.lib.utils import safe_traverse


def get_event(event_id):
    if not event_id:
        return None
    return Event.query.filter(Event.id == event_id, Event.deleted == 0).first()


def get_latest_pregnancy_event(client_id):
    return Event.query.join(EventType, rbRequestType).filter(
        Event.client_id == client_id,
        Event.deleted == 0,
        rbRequestType.code == request_type_pregnancy,
        Event.execDate.is_(None)
    ).order_by(Event.setDate.desc()).first()

def save_maternal_cert(cert_id, data):
    cert = MaternalCertificate.query.get_or_404(cert_id) if cert_id else MaternalCertificate()
    org_id = safe_traverse(data, 'lpu', 'id')
    cert.date = data.get('date')
    cert.number = data.get('number')
    cert.series = data.get('series')
    cert.event_id = data.get('event_id')
    cert.issuing_LPU_free_input = safe_traverse(data, 'lpu', 'short_name') if not org_id else None
    cert.issuing_LPU_id = org_id
    cert.deleted = data.get('deleted', 0)
    return cert
