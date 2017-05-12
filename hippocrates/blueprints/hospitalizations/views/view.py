# -*- coding: utf-8 -*-
from flask import render_template

from hippocrates.blueprints.hospitalizations.app import module


@module.route('/')
@module.route('/current')
def html_current_hosps():
    return render_template('hospitalizations/current_hosps.html')


@module.route('/search')
def html_search_hosps():
    return render_template('hospitalizations/search.html')

