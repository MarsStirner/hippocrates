# coding: utf-8

from nemesis.lib.utils import safe_traverse, safe_date
from nemesis.models.risar import MaternalCertificate


def save_maternal_cert(cert_id, data):
    cert = MaternalCertificate.query.get_or_404(cert_id) if cert_id else MaternalCertificate()
    org_id = safe_traverse(data, 'lpu', 'id')
    cert.date = safe_date(data.get('date'))
    cert.number = data.get('number')
    cert.series = data.get('series')
    cert.event_id = data.get('event_id')
    cert.issuing_LPU_free_input = safe_traverse(data, 'lpu', 'short_name') if not org_id else None
    cert.issuing_LPU_id = org_id
    return cert
