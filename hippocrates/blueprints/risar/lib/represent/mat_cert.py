# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


def represent_mat_cert(mat_cert):
    if not mat_cert:
        return None,
    return {
        'id': mat_cert.id,
        'date': mat_cert.date,
        'series': mat_cert.series,
        'number': mat_cert.number,
        'issuing_LPU_free_input': mat_cert.issuing_LPU_free_input,
        'issuing_LPU_id': mat_cert.issuing_LPU_id,
        'lpu': mat_cert.lpu,
        'event_id': mat_cert.event_id,
    }