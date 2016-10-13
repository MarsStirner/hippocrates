# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


def represent_mat_cert(mat_cert):
    return {
        'id': mat_cert.id if mat_cert else None,
        'date': mat_cert.date if mat_cert else None,
        'series': mat_cert.series if mat_cert else None,
        'number': mat_cert.number if mat_cert else None,
        'issuing_LPU_free_input': mat_cert.issuing_LPU_free_input if mat_cert else None,
        'issuing_LPU_id': mat_cert.issuing_LPU_id if mat_cert else None,
        'lpu': mat_cert.lpu if mat_cert else None,
        'event_id': mat_cert.event_id if mat_cert else None,
    }