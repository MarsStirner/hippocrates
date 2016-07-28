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
            'event': {
                'html': {
                    'event_info': url_for('event.html_event_info'),
                    'new_event': url_for('event.new_event'),
                    'request_type_kind': url_for('event.request_type_kind_choose'),
                },
                'event_get': url_for('event.api_event_info'),
                'event_new': url_for('event.api_event_new_get'),
                'event_save': url_for('event.api_event_save'),
                'event_close': url_for('event.api_event_close'),
                'event_actions': url_for('event.api_event_actions'),
                'moving_save': url_for('event.api_moving_save'),
                'moving_close': url_for('event.api_event_moving_close'),
                'hosp_beds': url_for('event.api_hosp_beds_get'),
                'lab_res_dynamics': url_for('event.api_event_lab_res_dynamics'),
                'blood_history': url_for('event.api_blood_history_save'),
                'event_stationary_open': url_for('event.api_event_stationary_open_get'),
                'diagnosis': url_for('event.api_diagnosis_get'),
                'delete_service': url_for('event.api_service_delete_service'),
                'delete_event': url_for('event.api_delete_event'),
                'get_events': url_for('event.api_get_events'),
            }
        }
    }