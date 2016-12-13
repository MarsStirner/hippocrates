# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flask_login import current_user
from safe import safe_traverse

from .config import MODULE_NAME, RUS_NAME
from nemesis.app import app as nemesis_app
from nemesis.lib.frontend import frontend_config
from hippocrates.blueprints.risar.lib.specific import SpecificsManager

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(
        module_name=RUS_NAME,
    )


@module.route('/config.js')
def config_js():
    return render_template('risar/config.js')


@module.route('/current_user.js')
def current_user_js():
    return render_template('risar/current_user.js', current_user=current_user.export_js())


@nemesis_app.context_processor
def risar_context_processors():
    return {
        'specifics_mng': SpecificsManager
    }


@frontend_config
def fc_risar_settings():
    """
    Настройки из конфигов, специфичные для РИСАР
    """
    nemesis_config = nemesis_app.config
    return {
        'local_config': {
            'risar': {
                'risar_regions': nemesis_config['RISAR_REGIONS'],
                'schedule': {
                    'external_schedule_url': safe_traverse(nemesis_config,
                                                           'system_prefs', 'integration', 'external_schedule_url'),
                },
                'extended_search': {
                    'common_access_curator': safe_traverse(nemesis_config, 'system_prefs', 'ui', 'extended_search',
                                                           'common_access_curator'),
                    'common_access_doctor': safe_traverse(nemesis_config, 'system_prefs', 'ui', 'extended_search',
                                                          'common_access_doctor'),
                },
            },
        }
    }

from .template_filters import *

# noinspection PyUnresolvedReferences
from .views import *
