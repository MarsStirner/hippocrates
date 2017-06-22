# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config, uf_placeholders
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )

# noinspection PyUnresolvedReferences
from .views import *


@frontend_config
def fc_urls():
    return {
        'url': {
            'actions': {
                'html': {
                    'action': url_for('actions.html_action'),
                    'actions_with_values_modal': uf_placeholders('actions.actions_with_values_modal', ['client_id']),
                },
                'action_get': uf_placeholders('actions.api_action_get', ['action_id']),
                'action_properties_get': uf_placeholders('actions.api_action_properties_get', ['action_id']),
                'action_new': uf_placeholders('actions.api_action_new_get', ['action_type_id', 'event_id']),
                'action_new_lab': uf_placeholders('actions.api_action_new_lab_get', ['action_type_id', 'event_id']),
                'action_save': uf_placeholders('actions.api_action_post', ['action_id']),
                'action_previous': url_for('actions.api_find_previous'),
                'autosave_normal': uf_placeholders('actions.api_action_autosave', ['action_id']),
                'autosave_new': uf_placeholders('actions.api_action_autosave_unsaved', ['event_id', 'action_type_id']),
                'rls_search': url_for('actions.api_search_rls'),
                'action_delete': uf_placeholders('actions.api_delete_action', ['action_id']),
                'atl_get_flat': url_for('actions.api_atl_get_flat'),
                'apt_groups_get': uf_placeholders('actions.api_apt_groups_get', ['action_type_id']),
                'action_html': url_for('actions.html_action'),
                'create_lab_direction': url_for('actions.api_create_lab_direction'),
                'get_action_ped': url_for('actions.api_get_action_ped'),
                'search_actions': url_for('actions.api_search_actions'),
                'patient_actions': url_for('actions.api_patient_actions'),
                'actions_with_values': uf_placeholders('actions.api_patient_actions', ['client_id']),
            }
        }
    }
