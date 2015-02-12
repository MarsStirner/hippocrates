# -*- coding: utf-8 -*-
from flask import render_template, abort
from jinja2 import TemplateNotFound

from ..app import module
from application.lib.utils import public_endpoint


__author__ = 'viruzzz-kun'


@module.route('/')
def index():
    try:
        return render_template('risar_config/index.html')
    except TemplateNotFound:
        abort(404)