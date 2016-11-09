# -*- coding: utf-8 -*-
import functools
from flask import render_template, request, redirect, url_for, abort
from flask_login import current_user

from hippocrates.blueprints.risar.risar_config import request_type_pregnancy, request_type_gynecological, \
    first_inspection_flat_code, second_inspection_flat_code, risar_gyn_checkup_flat_code, pc_inspection_flat_code, \
    puerpera_inspection_flat_code
from hippocrates.blueprints.risar.lib.card import AbstractCard
from nemesis.app import app
from nemesis.lib.utils import safe_int
from nemesis.models.actions import Action, ActionType
from nemesis.models.exists import rbRequestType
from nemesis.models.event import EventType, Event
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db
from ..app import module


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
    elif current_user.role_in('overseer3', 'ouz'):
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
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/event_routing.html', card=card)


def redirect_chart_if_possible(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        r_args = request.args.to_dict()
        ticket_id = r_args.pop('ticket_id', None)
        if ticket_id is not None:
            result = ScheduleClientTicket.query.filter(
                ScheduleClientTicket.id == ticket_id
            ).with_entities(
                ScheduleClientTicket.event_id
            ).first()
            if result and result[0]:
                return redirect(url_for(request.endpoint, event_id=result[0]))
        return func(*args, **kwargs)
    return wrapper


@module.route('/pregnancy-chart.html')
@redirect_chart_if_possible
def html_pregnancy_chart():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/chart.html', card=card)


@module.route('/gynecological-chart.html')
@redirect_chart_if_possible
def html_gynecological_chart():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/chart.html', card=card)


chart_mapping = {
    request_type_pregnancy: '.html_pregnancy_chart',
    request_type_gynecological: '.html_gynecological_chart',
}


@module.route('/auto-chart.html')
def html_auto_chart():
    if 'event_id' in request.args:
        event_id, request_type_code = request.args['event_id'], None
    elif 'ticket_id' in request.args:
        (event_id, request_type_code) = db.session.query(
            Event.id, rbRequestType.code
        ).join(
            EventType, rbRequestType, ScheduleClientTicket,
        ).filter(
            rbRequestType.code.in_([request_type_pregnancy, request_type_gynecological]),
            ScheduleClientTicket.id == request.args['ticket_id'],
        ).first() or (None, None)
    elif 'client_id' in request.args:
        client_id = request.args['client_id']
        # У нас есть незакрытый случай беременности?
        (event_id, request_type_code) = db.session.query(
            Event.id, rbRequestType.code
        ).join(
            EventType, rbRequestType
        ).filter(
            rbRequestType.code == request_type_pregnancy,
            Event.client_id == client_id,
            Event.deleted == 0,
        ).first() or (None, None)
        if not event_id:
            # Может, у нас есть незакрытая карта гинеколо?
            (event_id, request_type_code) = db.session.query(
                Event.id, rbRequestType.code
            ).join(
                EventType, rbRequestType
            ).filter(
                rbRequestType.code == request_type_gynecological,
                Event.client_id == client_id,
                Event.deleted == 0,
            ).first() or (None, None)
    else:
        raise abort(400, u'Невозможно определить тип карты по передаваемым параметрам')

    if event_id:
        if not request_type_code:
            request_type_code, = db.session.query(rbRequestType.code).join(EventType, Event).filter(
                Event.id == event_id,
                Event.deleted == 0,
            ).first() or (None,)
            if not request_type_code:
                raise abort(404, 'Event not found')
        kwargs = {'event_id': event_id}
    else:
        kwargs = request.args.to_dict()
        request_type_code = request_type_gynecological

    if request_type_code not in chart_mapping:
        raise abort(500, u'Невозможно определить тип карты по передаваемым параметрам')
    return redirect(url_for(chart_mapping[request_type_code], **kwargs))


@module.route('/anamnesis.html')
def html_anamnesis():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/anamnesis_view.html', card=card)


@module.route('/gynecological-anamnesis.html')
def html_gynecological_anamnesis():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/anamnesis_view.html', card=card)


@module.route('/anamnesis/mother_edit.html')
def html_anamnesis_mother_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/anamnesis_mother_edit.html', card=card)


@module.route('/gynecological-anamnesis/edit.html')
def html_gynecological_anamnesis_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/anamnesis_edit.html', card=card)


@module.route('/anamnesis/father_edit.html')
def html_anamnesis_father_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/anamnesis_father_edit.html', card=card)


@module.route('/gyn/inspection.html')
def html_gyn_inspection():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/inspection_view.html', card=card)


@module.route('/gyn/inspection_edit.html')
def html_gyn_inspection_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/inspection_edit.html', card=card)


@module.route('/inspection.html')
def html_inspection():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/inspection_view.html', card=card)


@module.route('/inspection/gravidograma.html')
def html_gravidograma():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/gravidograma.html', card=card)


@module.route('/inspection_read.html')
def html_inspection_read():
    checkup_id = request.args.get('checkup_id')
    if not checkup_id:
        raise abort(404)

    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)

    checkup = Action.query.join(
        ActionType
    ).filter(
        Action.id == checkup_id
    ).with_entities(
        ActionType.flatCode
    ).first()

    if not checkup:
        abort(404)
    flat_code = checkup[0]

    if flat_code == first_inspection_flat_code:
        return render_template('risar/inspection_first_read.html', card=card)
    elif flat_code == second_inspection_flat_code:
        return render_template('risar/inspection_second_read.html', card=card)
    elif flat_code == risar_gyn_checkup_flat_code:
        return render_template('risar/unpregnant/inspection_read.html', card=card)
    elif flat_code == pc_inspection_flat_code:
        return render_template('risar/inspection_pc_read.html', card=card)
    elif flat_code == puerpera_inspection_flat_code:
        return render_template('risar/inspection_puerpera_read.html', card=card)


@module.route('/inspection_edit.html')
def html_inspection_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.join(
            ActionType
        ).filter(
            Action.id == checkup_id
        ).with_entities(
            ActionType.flatCode, Action.endDate
        ).first()

        if not checkup:
            abort(404)

        if checkup[1]:
            return redirect(url_for('.html_inspection_read', event_id=event_id, checkup_id=checkup_id, card=card))

        flat_code = checkup[0]
    else:
        first_inspection_exists = Action.query.join(ActionType).filter(
            Action.event_id == event_id,
            Action.deleted == 0,
            ActionType.flatCode == first_inspection_flat_code,
        ).count() > 0
        flat_code = second_inspection_flat_code if first_inspection_exists else first_inspection_flat_code
    
    if flat_code == first_inspection_flat_code:
        return render_template('risar/inspection_first_edit.html', card=card)
    
    elif flat_code == second_inspection_flat_code:
        return render_template('risar/inspection_second_edit.html', card=card)
    

@module.route('/inspection_pc_edit.html')
def html_inspection_pc_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.filter(
            Action.id == checkup_id
        ).with_entities(
            Action.endDate
        ).first()

        if not checkup:
            abort(404)

        if checkup[0]:
            return redirect(url_for('.html_inspection_read', event_id=event_id, checkup_id=checkup_id, event=card))
    return render_template('risar/inspection_pc_edit.html', card=card)


@module.route('/inspection_puerpera.html')
def html_inspection_puerpera():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/inspection_puerpera_view.html', event=card)


@module.route('/inspection_puerpera_edit.html')
def html_inspection_puerpera_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    checkup_id = request.args.get('checkup_id')
    if checkup_id:
        checkup = Action.query.filter(
            Action.id == checkup_id
        ).with_entities(
            Action.endDate
        ).first()

        if not checkup:
            abort(404)

        if checkup[0]:
            return redirect(url_for('.html_inspection_read', event_id=event_id, checkup_id=checkup_id, event=card))
    return render_template('risar/inspection_puerpera_edit.html', event=card)


@module.route('/inspection_fetus.html')
def html_inspection_fetus():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/inspection_fetus_view.html', card=card)


@module.route('/epicrisis.html')
def html_epicrisis():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/epicrisis.html', card=card)


@module.route('/epicrisis_edit.html')
def html_epicrisis_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/epicrisis_edit.html', card=card)


@module.route('/event_diagnoses.html')
def html_event_diagnoses():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/event_diagnoses.html', card=card)


@module.route('/ambulance_patient_info.html')
def html_ambulance_patient_info():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/ambulance_patient_info.html', card=card)


@module.route('/measure_list.html')
def html_event_measure():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/event_measure_list.html', card=card)


@module.route('/gynecological-measure_list.html')
def html_gynecological_event_measure():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/unpregnant/event_measure_list.html', card=card)


@module.route('/stats/org-birth-care/')
def html_stats_org_birth_care():
    return render_template('risar/stats/obcl_orgs.html')


@module.route('/errands/errands_list.html')
def html_errands_list():
    return render_template('risar/errands/errands_list.html')


@module.route('/card_fill_history.html')
def html_card_fill_history():
    args = request.args.to_dict()
    event_id = safe_int(args.get('event_id'))
    if not event_id:
        raise abort(404)
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/card_fill_history.html', card=card)


@module.route('/risk_groups_list.html')
def html_risk_groups_list():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/risk_groups_list.html', card=card)


@module.route('/concilium_list.html')
def html_concilium_list():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/concilium_list.html', card=card)


@module.route('/concilium.html')
def html_concilium():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/concilium.html', card=card)


@module.route('/radzinsky_risks.html')
def html_radzinsky_risks():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/radzinsky_risks.html', card=card)


@module.route('/soc_prof_help.html')
def html_soc_prof_help():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/soc_prof_help.html', card=card)


@module.route('/nursing.html')
def html_postpartal_nursing():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/postpartal_nursing_view.html',
                           card=card)


@module.route('/nursing_edit.html')
def html_postpartal_nursing_edit():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    pp_nursing_id = request.args.get('pp_nursing_id')

    if pp_nursing_id:
        nursing = Action.query.filter(
            Action.id == pp_nursing_id
        ).with_entities(
            Action.endDate
        ).first()

        if not nursing:
            abort(404)

        if nursing[0]:
            return redirect(url_for('.html_postpartal_nursing_read', event_id=event_id,
                                            pp_nursing_id=pp_nursing_id))

    return render_template('risar/postpartal_nursing_edit.html',
                           card=card)


@module.route('/nursing_read.html')
def html_postpartal_nursing_read():
    event_id = safe_int(request.args.get('event_id'))
    card = AbstractCard.get_by_id(event_id)
    return render_template('risar/postpartal_nursing_read.html', card=card)


