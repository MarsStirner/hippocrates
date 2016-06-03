# -*- coding: utf-8 -*-
from flask import Blueprint, url_for
from nemesis.lib.frontend import frontend_config
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
            'schedule': {
                'html': {
                    'appointment': url_for('schedule.appointment'),
                    'index': url_for('schedule.index'),
                    'person_monthview': url_for('schedule.person_schedule_monthview'),
                    'day_free': url_for('schedule.html_day_free'),
                },

                'appointment': url_for('schedule.api_appointment'),
                'schedule': url_for('schedule.api_schedule'),
                'move_client': url_for('schedule.api_move_client'),
                'schedule_description': url_for('schedule.api_schedule_description'),
                'copy_schedule_description': url_for('schedule.api_copy_schedule_description'),
                'schedule_lock': url_for('schedule.api_schedule_lock'),
                'persons_tree': url_for('schedule.api_all_persons_tree'),
                'day_schedule': url_for('schedule.api_day_schedule'),
                'get_orgstructure': url_for('schedule.api_org_structure'),
                'persons_tree_schedule_info': url_for('schedule.api_persons_tree_schedule_info'),
                'search_persons': url_for('schedule.api_search_persons'),
                'procedure_offices': url_for('schedule.api_procedure_offices_get'),
            }
        }
    }