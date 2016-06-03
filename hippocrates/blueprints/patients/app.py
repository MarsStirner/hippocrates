# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(module_name=RUS_NAME)


# noinspection PyUnresolvedReferences
from .views import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'patients': {
                'client_get': url_for('patients.api_patient_get'),
                'client_save': url_for('patients.api_patient_save'),
                'client_html': url_for('patients.patient'),
                'client_search': url_for('patients.api_search_clients'),
                'client_events': url_for('patients.api_patient_events_get'),
                'client_vmp_coupons': url_for('patients.api_patient_get_vmpcoupons'),
                'client_info_full': url_for('patients.patient_info_full'),
                'coupon_parse': url_for('patients.api_patient_coupon_parse'),
                'coupon_save': url_for('patients.api_patient_coupon_save'),
                'coupon_delete': url_for('patients.api_patient_coupon_delete'),
            }
        }
    }
