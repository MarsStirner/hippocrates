# -*- coding: utf-8 -*-
from flask import render_template, request
from ..app import module
from application.models.actions import Action, ActionType

__author__ = 'mmalkov'


@module.route('/')
@module.route('/index.html')
def index_html():
    return render_template('risar/index.html')


@module.route('/search.html')
def html_search():
    return render_template('risar/search.html')


@module.route('/routing.html')
def html_routing():
    return render_template('risar/event_routing.html')


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


@module.route('/inspection/gravidograma.html')
def html_gravidograma():
    return render_template('risar/gravidograma.html')


@module.route('/inspection_edit.html')
def html_inspection_edit():
    event_id = request.args['event_id']
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.get(checkup_id)
        flat_code = checkup.actionType.flatCode
    else:
        first_inspection = Action.query.join(ActionType).filter(Action.event_id == event_id, Action.deleted == 0,
                                                               ActionType.flatCode == 'risarFirstInspection').first()
        flat_code = 'risarSecondInspection' if first_inspection else 'risarFirstInspection'
    if flat_code == 'risarFirstInspection':
        return render_template('risar/inspection_first_edit.html')
    elif flat_code == 'risarSecondInspection':
        return render_template('risar/inspection_second_edit.html')


@module.route('/epicrisis.html')
def html_epicrisis():
    return render_template('risar/epicrisis.html')


@module.route('/epicrisis_edit.html')
def html_epicrisis_edit():
    return render_template('risar/epicrisis_edit.html')


@module.route('/event_diagnoses.html')
def html_event_diagnoses():
    return render_template('risar/event_diagnoses.html')