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
            'useraccount': {
                'user_mail_summary': url_for("useraccount.api_mail_summary"),
                'user_mail': url_for("useraccount.api_mail_get") + '{0}',
                'user_mail_alter': url_for("useraccount.api_mail_mark") + '{0}/{1}',
                'subscription': url_for("useraccount.api_subscription") + '{0}',
            },
        }
    }
