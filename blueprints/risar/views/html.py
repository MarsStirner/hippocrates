# -*- coding: utf-8 -*-
from flask import render_template, request
from ..app import module
from application.models.actions import Action

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


@module.route('/anamnesis/mother_edit.html')
def html_anamnesis_mother_edit():
    return render_template('risar/anamnesis_mother_edit.html')


@module.route('/anamnesis/father_edit.html')
def html_anamnesis_father_edit():
    return render_template('risar/anamnesis_father_edit.html')


@module.route('/inspection.html')
def html_inspection():
    return render_template('risar/inspection_view.html')


@module.route('/inspection_edit.html')
def html_inspection_edit():
    checkup_id = request.args['checkup_id']
    checkup = Action.query.get(checkup_id)
    flat_code = checkup.actionType.flatCode
    if flat_code == 'risarFirstInspection':
        return render_template('risar/inspection_first_edit.html')
    elif flat_code == 'risarSecondInspection':
        return render_template('risar/inspection_second_edit.html')