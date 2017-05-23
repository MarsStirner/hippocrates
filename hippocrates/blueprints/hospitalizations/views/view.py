# -*- coding: utf-8 -*-
from flask import render_template

from hippocrates.blueprints.hospitalizations.app import module


@module.route('/')
@module.route('/search')
def html_search_hosps():
    return render_template('hospitalizations/search_hosps.html')

