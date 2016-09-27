# -*- coding: utf-8 -*-

from flask import render_template, request, redirect, url_for, abort
from flask.ext.login import current_user

from blueprints.risar.lib.debug import get_debug_data
from nemesis.app import app
from nemesis.lib.utils import safe_int
from nemesis.models.actions import Action, ActionType
from nemesis.lib.settings import Settings
from ..app import module
from blueprints.risar.lib.chart import get_event

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


@module.route('/mis')
def html_mis():
    return render_template(app.config['INDEX_HTML'])


@module.route('/search.html')
def html_search():
    return render_template('risar/search.html')


@module.route('/routing.html')
def html_routing():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/event_routing.html', event=event)


@module.route('/chart.html')
def html_chart():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    debug_data = get_debug_data(request.args)
    return render_template('risar/chart.html', event=event, debug_data=debug_data)


@module.route('/anamnesis.html')
def html_anamnesis():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/anamnesis_view.html', event=event)


@module.route('/anamnesis/mother_edit.html')
def html_anamnesis_mother_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/anamnesis_mother_edit.html', event=event)


@module.route('/anamnesis/father_edit.html')
def html_anamnesis_father_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/anamnesis_father_edit.html', event=event)


@module.route('/inspection.html')
def html_inspection():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/inspection_view.html', event=event)


@module.route('/inspection/gravidograma.html')
def html_gravidograma():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/gravidograma.html', event=event)


@module.route('/inspection_read.html')
def html_inspection_read():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    flat_code = None
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.get(checkup_id)
        flat_code = checkup.actionType.flatCode
    if flat_code == 'risarFirstInspection':
        return render_template('risar/inspection_first_read.html', event=event)
    elif flat_code == 'risarSecondInspection':
        return render_template('risar/inspection_second_read.html', event=event)


@module.route('/inspection_edit.html')
def html_inspection_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    debug_data = get_debug_data(request.args)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.get(checkup_id)
        flat_code = checkup.actionType.flatCode
        if checkup.endDate:
            return redirect(url_for('.html_inspection_read', event_id=event_id, checkup_id=checkup_id))
    else:
        first_inspection = Action.query.join(ActionType).filter(Action.event_id == event_id, Action.deleted == 0,
                                                               ActionType.flatCode == 'risarFirstInspection').first()
        flat_code = 'risarSecondInspection' if first_inspection else 'risarFirstInspection'
    if flat_code == 'risarFirstInspection':
        return render_template('risar/inspection_first_edit.html', event=event, debug_data=debug_data)
    elif flat_code == 'risarSecondInspection':
        return render_template('risar/inspection_second_edit.html', event=event, debug_data=debug_data)


@module.route('/inspection_pc_read.html')
def html_inspection_pc_read():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/inspection_pc_read.html', event=event)


@module.route('/inspection_pc_edit.html')
def html_inspection_pc_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    debug_data = get_debug_data(request.args)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.get(checkup_id)
        if checkup.endDate:
            return redirect(url_for('.html_inspection_pc_read', event_id=event_id, checkup_id=checkup_id))
    return render_template('risar/inspection_pc_edit.html', event=event, debug_data=debug_data)


@module.route('/inspection_puerpera.html')
def html_inspection_puerpera():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/inspection_puerpera_view.html', event=event)


@module.route('/inspection_puerpera_read.html')
def html_inspection_puerpera_read():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/inspection_puerpera_read.html', event=event)


@module.route('/inspection_puerpera_edit.html')
def html_inspection_puerpera_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    debug_data = get_debug_data(request.args)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.get(checkup_id)
        if checkup.endDate:
            return redirect(url_for('.html_inspection_puerpera_read', event_id=event_id, checkup_id=checkup_id))
    return render_template('risar/inspection_puerpera_edit.html', event=event, debug_data=debug_data)


@module.route('/inspection_fetus.html')
def html_inspection_fetus():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/inspection_fetus_view.html', event=event)


@module.route('/epicrisis.html')
def html_epicrisis():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/epicrisis.html', event=event)


@module.route('/epicrisis_edit.html')
def html_epicrisis_edit():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/epicrisis_edit.html', event=event)


@module.route('/event_diagnoses.html')
def html_event_diagnoses():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/event_diagnoses.html', event=event)


@module.route('/ambulance_patient_info.html')
def html_ambulance_patient_info():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/ambulance_patient_info.html', event=event)


@module.route('/measure_list.html')
def html_event_measure():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/event_measure_list.html', event=event)


@module.route('/stats/org-birth-care/')
def html_stats_org_birth_care():
    return render_template('risar/stats/obcl_orgs.html')


@module.route('/stats/org-curation/')
def html_stats_org_curation():
    return render_template('risar/stats/org_curation.html')


@module.route('/errands/errands_list.html')
def html_errands_list():
    return render_template('risar/errands/errands_list.html')


@module.route('/card_fill_history.html')
def html_card_fill_history():
    args = request.args.to_dict()
    event_id = safe_int(args.get('event_id'))
    if not event_id:
        raise abort(404)
    event = get_event(event_id)
    return render_template('risar/card_fill_history.html', event=event)


@module.route('/risk_groups_list.html')
def html_risk_groups_list():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/risk_groups_list.html', event=event)


@module.route('/concilium_list.html')
def html_concilium_list():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/concilium_list.html', event=event)


@module.route('/concilium.html')
def html_concilium():
    event_id = safe_int(request.args.get('event_id'))
    event = get_event(event_id)
    return render_template('risar/concilium.html', event=event)
