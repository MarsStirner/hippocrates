# -*- coding: utf-8 -*-

from flask import request, abort
from nemesis.lib.html_utils import UIException
from ..app import module
from nemesis.lib.settings import Settings

__all__ = ['api', 'html']

__author__ = 'mmalkov'


@module.before_request
def before_risar_request():
    settings = Settings()
    if not (
        request.is_xhr or
        'static' in request.endpoint or
        'config_js' in request.endpoint or
        settings.getBool('RISAR.Enabled', False)
    ):
        raise UIException(403, u'Поддержка РИСАР не включена')
