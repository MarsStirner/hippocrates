# -*- coding: utf-8 -*-
from flask import render_template, request
from flask.ext.login import current_user
from ..app import module
from nemesis.models.actions import Action, ActionType

__author__ = 'mmalkov'


@module.route('/')
@module.route('/index.html')
def index_html():
    if current_user.role_in('ambulance'):
        return render_template('risar/desktop/index_ambulance.html')
    elif current_user.role_in('admin', 'obstetrician'):
        return render_template('risar/desktop/index_obstetrician.html')
    elif current_user.role_in('overseer1'):
        return render_template('risar/desktop/index_overseer1.html')
    elif current_user.role_in('overseer2'):
        return render_template('risar/desktop/index_overseer2.html')
    elif current_user.role_in('overseer3'):
        return render_template('risar/desktop/index_overseer3.html')
    else:
        return render_template('risar/desktop/index.html')


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


@module.route('/ambulance_patient_info.html')
def html_ambulance_patient_info():
    return render_template('risar/ambulance_patient_info.html')


@module.route('/measure_list.html')
def html_event_measure():
    return render_template('risar/event_measure_list.html')


@module.route('/stats/org-birth-care/')
def html_stats_org_birth_care():
    return render_template('risar/stats/obcl_orgs.html')


@module.route('/stats/org-curation/')
def html_stats_org_curation():
    return render_template('risar/stats/org_curation.html')


@module.route('/errands/errands_list.html')
def html_errands_list():
    return render_template('risar/errands/errands_list.html')