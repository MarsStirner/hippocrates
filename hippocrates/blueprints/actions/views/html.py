# -*- coding: utf-8 -*-
from flask import render_template
from ..app import module

__author__ = 'viruzzz-kun'


@module.route('/action.html')
def html_action():
    return render_template(
        'actions/action.html'
    )