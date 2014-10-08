# -*- coding: utf-8 -*-
from flask import render_template, request
from ..app import module

__author__ = 'mmalkov'


@module.route('/')
@module.route('/index.html')
def index_html():
    return render_template('risar/index.html')


@module.route('/chart.html')
def html_chart():
    return render_template('risar/chart.html')


@module.route('/anamnesis.html')
def html_anamnesis():
    return render_template('risar/anamnesis_view.html')


@module.route('/anamnesis_edit.html')
def html_anamnesis_edit():
    return render_template('risar/anamnesis_edit.html')