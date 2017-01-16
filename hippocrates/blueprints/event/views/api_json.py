# -*- coding: utf-8 -*-

import datetime
import logging
import blinker
import collections

from hippocrates.blueprints.event.app import module
from hippocrates.blueprints.event.lib.utils import (EventSaveException, save_event, received_save, client_quota_save,
                                        save_executives, EventSaveController, MovingController, received_close)
from hippocrates.blueprints.patients.lib.utils import add_or_update_blood_type
from flask import request, abort
from nemesis.lib.agesex import recordAcceptableEx
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.const import STATIONARY_EVENT_CODES, POLICLINIC_EVENT_CODES, DIAGNOSTIC_EVENT_CODES
from nemesis.lib.data import get_planned_end_datetime, int_get_atl_dict_all, _get_stationary_location_query
from nemesis.lib.event.event_builder import PoliclinicEventBuilder, StationaryEventBuilder, EventConstructionDirector
from nemesis.lib.jsonify import EventVisualizer, StationaryEventVisualizer
from nemesis.lib.sphinx_search import SearchEventService, SearchEvent
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import (safe_traverse, safe_date, safe_datetime, get_utc_datetime_with_tz, safe_int,
                               parse_id, bail_out)
from nemesis.models.accounting import Service, Contract, Invoice, InvoiceItem
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, OrgStructure_HospitalBed, ActionProperty_HospitalBed, \
    Action_TakenTissueJournalAssoc, TakenTissueJournal
from nemesis.models.client import Client
from nemesis.models.diagnosis import Diagnosis, Diagnostic
from nemesis.models.event import (Event, EventType, Visit, Event_Persons)
from nemesis.models.exists import Person, rbRequestType, rbResult, OrgStructure, MKB, rbTest
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.systemwide import db
from nemesis.lib.mq_integration.event import MQOpsEvent, notify_event_changed, notify_moving_changed
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import joinedload

logger = logging.getLogger('simple')


@module.route('/api/event_info.json')
@api_method
def api_event_info():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    if event.is_stationary:
        vis = StationaryEventVisualizer()
    else:
        vis = EventVisualizer()
    return vis.make_event_info_for_current_role(event)


@module.route('/api/event_new.json', methods=['GET'])
@api_method
def api_event_new_get():
    ticket_id = safe_int(request.args.get('ticket_id'))
    client_id = safe_int(request.args['client_id'])
    request_type_kind = request.args['request_type_kind']
    v = EventVisualizer()
    if request_type_kind == 'policlinic':
        event_builder = PoliclinicEventBuilder(client_id, ticket_id)
    elif request_type_kind == 'stationary':
        event_builder = StationaryEventBuilder(client_id, ticket_id)
        v = StationaryEventVisualizer()
    event_construction_director = EventConstructionDirector()
    event_construction_director.set_builder(event_builder)
    event = event_construction_director.construct()
    return v.make_new_event(event)


@module.route('/api/event_stationary_opened.json', methods=['GET'])
@api_method
def api_event_stationary_open_get():
    client_id = int(request.args['client_id'])
    events = Event.query.join(EventType, rbRequestType).filter(
        Event.client_id == client_id,
        Event.execDate.is_(None),
        Event.deleted == 0,
        rbRequestType.code.in_(STATIONARY_EVENT_CODES)
    ).order_by(Event.setDate.desc())
    v = EventVisualizer()
    return map(v.make_short_event, events)


@module.route('/api/event_save.json', methods=['POST'])
@api_method
def api_event_save():
    result = {}
    all_data = request.json
    request_type_kind = all_data.get('request_type_kind')
    event_data = all_data.get('event')
    event_id = event_data.get('id')
    create_mode = not event_id

    event_ctrl = EventSaveController()
    if event_id:
        event = Event.query.get(event_id)
        if not event:
            raise ApiException(404, u'Не найдено обращение с id = {}'.format(event_id))
        event_data = all_data['event']
        event = event_ctrl.update_base_info(event, event_data)
        event_ctrl.store(event)
    else:
        event = Event()
        event = event_ctrl.create_base_info(event, all_data)
        error_msg = {}
        if not UserUtils.can_create_event(event, error_msg):
            raise ApiException(403, u'Невозможно создать обращение: %s.' % error_msg['message'])
        event_ctrl.store(event)
        event_id = int(event)
        if request_type_kind == 'policlinic':
            visit = Visit.make_default(event)
            db.session.add(visit)
            db.session.commit()

    result['id'] = int(event)

    update_executives(event)

    if request_type_kind == 'stationary':
        received_data = all_data['received']
        quota_data = all_data['vmp_quoting']
        received_save(event_id, received_data)
        if quota_data:
            client_quota_save(event, quota_data)

    if create_mode:
        notify_event_changed(MQOpsEvent.create, event)

    return result


@module.route('/api/event_moving_save.json', methods=['POST'])
@api_method
def api_moving_save():
    vis = StationaryEventVisualizer()
    mov_ctrl = MovingController()
    data = request.json
    event_id = data.get('event_id')
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Не найдено обращение с id = {}'.format(event_id))
    moving_id = data.get('id')
    create_mode = not moving_id
    if moving_id:
        moving = Action.query.get(moving_id)
        if not moving:
            raise ApiException(404, u'Не найдено движение с id = {}'.format(moving_id))
        moving = mov_ctrl.update_moving_data(moving, data)
        result = vis.make_moving_info(moving)
    else:
        result = mov_ctrl.create_moving(event_id, data)
        moving = result[1]
        result = map(vis.make_moving_info, result)
    received_close(event)

    if not create_mode:
        notify_moving_changed(MQOpsEvent.moving, moving)

    return result


@module.route('/api/event_moving_close.json', methods=['POST'])
@api_method
def api_event_moving_close():
    vis = StationaryEventVisualizer()
    mov_ctrl = MovingController()
    moving_info = request.json
    moving_id = moving_info['id']
    if not moving_id:
        raise ApiException(404, u'Не передан параметр moving_id')
    moving = Action.query.get(moving_id)
    if not moving:
        raise ApiException(404, u'Не найдено движение с id = {}'.format(moving_id))
    moving = mov_ctrl.close_moving(moving)
    return vis.make_moving_info(moving)


@module.route('/api/event_lab-res-dynamics.json', methods=['GET'])
@api_method
def api_event_lab_res_dynamics():
    # динамика по тестам в действиях с одинаковым ActionType
    event_id = request.args.get('event_id') or bail_out(ApiException(400, u'event_id должен быть указан'))
    action_type_id = request.args.get('action_type_id') or bail_out(ApiException(400, u'action_type_id должен быть указан'))
    from_date = safe_date(request.args.get('from_date', datetime.date.today() - datetime.timedelta(5)))
    to_date = safe_date(request.args.get('to_date', datetime.date.today()))

    rb_tests_subquery = rbTest.query.join(
        ActionPropertyType
    ).filter(
        ActionPropertyType.actionType_id == action_type_id
    ).with_entities(rbTest.id).subquery()

    EventSelf = db.aliased(Event)

    query = ActionProperty.query.join(
        ActionPropertyType,
        Action,
        Event,
    ).join(
        EventSelf, db.and_(
            EventSelf.client_id == Event.client_id,
            EventSelf.id == event_id,
        ),
    ).filter(
        Action.deleted == 0,
        func.date(Action.begDate) >= from_date,
        func.date(Action.begDate) <= to_date,
        ActionProperty.deleted == 0,
        ActionPropertyType.test_id.in_(rb_tests_subquery),
    )

    tissue_query = Action.query.outerjoin(
        Action_TakenTissueJournalAssoc, Action_TakenTissueJournalAssoc.action_id == Action.id
    ).outerjoin(
        TakenTissueJournal, TakenTissueJournal.id.in_([
            Action_TakenTissueJournalAssoc.takenTissueJournal_id,
            Action.takenTissueJournal_id,
        ])
    ).filter(
        Action.id.in_(query.group_by(ActionProperty.action_id).with_entities(ActionProperty.action_id).subquery())
    ).group_by(
        Action.id
    ).with_entities(
        Action.id,
        func.coalesce(TakenTissueJournal.datetimeTaken, TakenTissueJournal.datetimePlanned, Action.plannedEndDate, Action.endDate, Action.begDate)
    )

    tissue_dict = dict(tissue_query)

    dynamics = collections.defaultdict(lambda: {'test_name': '', 'values': {}})
    dates = set()
    result = query.join(
        Action.actionType,
        ActionPropertyType.test,
    ).order_by(Action.begDate).with_entities(
        ActionProperty,
        rbTest
    )

    for (prop, test) in result:
        if prop.value and tissue_dict[prop.action_id]:
            date = tissue_dict[prop.action_id].strftime('%d.%m.%Y %H:%M')
            dates.add(date)
            dynamics[test.id]['test_name'] = test.name
            dynamics[test.id]['values'][date] = prop.value
    return sorted(dates), dynamics


@module.route('/api/event_hosp_beds_get.json', methods=['GET'])
@api_method
def api_hosp_beds_get():
    vis = StationaryEventVisualizer()
    org_str_id = request.args.get('org_str_id')
    hb_id = request.args.get('hb_id')
    ap_hosp_beds = ActionProperty.query.join(ActionPropertyType, Action, ActionType, Event,
                                             ActionProperty_HospitalBed, OrgStructure_HospitalBed)\
        .filter(ActionProperty.deleted == 0, ActionPropertyType.code == 'hospitalBed', Action.deleted == 0,
                Event.deleted == 0, ActionType.flatCode == 'moving',
                db.or_(Action.endDate.is_(None), Action.endDate >= datetime.datetime.now()), OrgStructure_HospitalBed.master_id == org_str_id).all()
    occupied_hb = [ap.value for ap in ap_hosp_beds]
    all_hb = OrgStructure_HospitalBed.query.filter(OrgStructure_HospitalBed.master_id == org_str_id).all()
    for hb in all_hb:
        hb.occupied = True if hb in occupied_hb else False
        hb.chosen = True if (hb_id and hb.id == hb_id) else False
    return map(vis.make_hosp_bed, all_hb)


@module.route('/api/blood_history_save.json', methods=['POST'])
@api_method
def api_blood_history_save():
    vis = StationaryEventVisualizer()
    data = request.json
    blood_type_info = data.get('blood_type_info')
    client_id = data.get('client_id')
    client = Client.query.get(client_id)
    bt = add_or_update_blood_type(client, blood_type_info)
    db.session.add(bt)
    db.session.commit()
    return vis.make_blood_history(bt)


def update_executives(event):
    last_executive = Event_Persons.query.filter(Event_Persons.event_id == event.id).order_by(desc(Event_Persons.begDate)).first()
    if not last_executive or last_executive.person_id != event.execPerson_id:
        executives = Event_Persons()
        executives.person = event.execPerson
        executives.event = event
        executives.begDate = event.setDate
        db.session.add(executives)
        if last_executive:
            last_executive.endDate = event.setDate
            db.session.add(last_executive)
        db.session.commit()


@module.route('/api/event_close.json', methods=['POST'])
@api_method
def api_event_close():
    all_data = request.json
    event_data = all_data['event']
    event_id = event_data['id']
    event = Event.query.get(event_id)

    error_msg = {}
    if not UserUtils.can_close_event(event, error_msg):
        raise ApiException(403, u'Невозможно закрыть обращение: %s.' % error_msg['message'])

    if not event_data['exec_date']:
        event_data['exec_date'] = get_utc_datetime_with_tz().isoformat()
    save_event(event_id, all_data)
    save_executives(event_id)

    notify_event_changed(MQOpsEvent.close, event)

    return {'result_name': u'Обращение закрыто'}


@module.route('/api/diagnosis.json', methods=['POST'])
@api_method
def api_diagnosis_save():
    current_datetime = datetime.datetime.now()
    data = request.json
    diagnosis_id = data.get('diagnosis_id')
    diagnostic_id = data.get('diagnostic_id')
    if diagnosis_id:
        diagnosis = Diagnosis.query.get(diagnosis_id)
    else:
        diagnosis = Diagnosis()
        diagnosis.createDatetime = current_datetime
    if diagnostic_id:
        diagnostic = Diagnostic.query.get(diagnostic_id)
    else:
        diagnostic = Diagnostic()
        diagnostic.createDatetime = current_datetime

    diagnosis.modifyDatetime = current_datetime
    diagnostic.modifyDatetime = current_datetime

    diagnosis.client_id = data['client_id']
    diagnosis.person_id = data['person']['id']
    diagnosis.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnosis.character_id = safe_traverse(data, 'character', 'id')
    diagnosis.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnosis.traumaType_id = safe_traverse(data, 'trauma', 'id')
    diagnosis.MKB = safe_traverse(data, 'mkb', 'code') or ''
    diagnosis.MKBEx = safe_traverse(data, 'mkb_ex', 'code') or ''
    if not diagnosis.endDate:
        diagnosis.endDate = current_datetime
    db.session.add(diagnosis)

    diagnostic.event_id = data['event_id']
    diagnostic.diagnosis = diagnosis
    diagnostic.diagnosisType_id = safe_traverse(data, 'diagnosis_type', 'id')
    diagnostic.character_id = safe_traverse(data, 'character', 'id')
    diagnostic.stage_id = safe_traverse(data, 'stage', 'id')
    diagnostic.phase_id = safe_traverse(data, 'phase', 'id')
    diagnostic.dispanser_id = safe_traverse(data, 'dispanser', 'id')
    diagnostic.traumaType_id = safe_traverse(data, 'trauma', 'id')
    diagnostic.healthGroup_id = safe_traverse(data, 'health_group', 'id')
    diagnostic.result_id = safe_traverse(data, 'result', 'id')
    diagnostic.notes = data.get('notes', '')
    diagnostic.sanatorium = 0
    diagnostic.hospital = 0
    diagnostic.speciality_id = 1
    diagnostic.version = 0
    diagnostic.rbAcheResult_id = safe_traverse(data, 'ache_result', 'id')
    if not diagnostic.setDate:
        diagnostic.setDate = current_datetime
    db.session.add(diagnostic)

    db.session.commit()


@module.route('/api/diagnosis.json', methods=['DELETE'])
@api_method
def api_diagnosis_delete():
    data = request.json
    if data['diagnosis_id']:
        Diagnosis.query.filter(Diagnosis.id == data['diagnosis_id']).update({'deleted': 1})
    if data['diagnostic_id']:
        Diagnostic.query.filter(Diagnostic.id == data['diagnostic_id']).update({'deleted': 1})
    db.session.commit()


@module.route('/api/diagnosis', methods=['GET'])
@api_method
def api_diagnosis_get():
    event_id = int(request.args['event_id'])
    event = Event.query.get(event_id)
    vis = EventVisualizer()
    return vis.make_diagnoses(event)


@module.route('/api/service/service_price.json', methods=['GET'])
@api_method
def api_search_services():
    query = request.args['q']
    client_id = request.args['client_id']
    event_type_id = request.args.get('event_type_id')
    contract_id = request.args.get('contract_id')
    person_id = request.args.get('person_id')
    speciality_id = None
    if person_id:
        doctor = Person.query.get(int(person_id))
        speciality_id = doctor.speciality_id
    result = SearchEventService.search(query,
                                       eventType_id=event_type_id,
                                       contract_id=contract_id,
                                       speciality_id=speciality_id)

    ats_apts = int_get_atl_dict_all()
    client = Client.query.get(client_id)
    client_age = client.age_tuple(datetime.date.today())

    def make_response(service_data):
        at_id = service_data['action_type_id']
        at_data = ats_apts.get(at_id)
        if not at_data:
            return None

        if not recordAcceptableEx(client.sexCode, client_age, at_data[6], at_data[5]):
            return None

        service = {
            'at_id': at_id,
            'code': service_data['ct_code'],
            'name': service_data['ct_name'],
            'at_code': service_data['at_code'],
            'at_name': service_data['at_name'],
            'price': service_data['price'],
            'is_lab': False
        }

        if at_data[9]:
            prop_types = at_data[9]
            prop_types = [prop_type[:2] for prop_type in prop_types if recordAcceptableEx(client.sexCode,
                                                                                          client_age,
                                                                                          prop_type[3],
                                                                                          prop_type[2])]
            if prop_types:
                service['is_lab'] = True
                service['assignable'] = prop_types
                service['all_assigned'] = map(lambda p: p[0], service['assignable'])
                service['all_planned_end_date'] = get_planned_end_datetime(at_id)
        return service

    matched = []
    for item in result['result']['items']:
        s = make_response(item)
        if s is not None:
            matched.append(s)

    return matched


@module.route('/api/event_payment/delete_service.json', methods=['POST'])
@api_method
def api_service_delete_service():
    # TODO: validations
    action_ids = request.json['action_id_list']
    if action_ids:
        actions = Action.query.filter(Action.id.in_(action_ids))
        actions.update({Action.deleted: 1},
                       synchronize_session=False)
        db.session.commit()


@module.route('/api/delete_event.json', methods=['POST'])
@api_method
def api_delete_event():
    event_id = parse_id(request.json, 'event_id')
    if event_id is None:
        raise ApiException(400, u'event_id должен быть числом')
    event = Event.query.get(event_id) or bail_out(ApiException(404, u'Обращение не найдено'))

    msg = {}
    if UserUtils.can_delete_event(event, msg):
        event.deleted = 1
        db.session.add(event)
        db.session.query(Action).filter(
            Action.event_id == event.id
        ).update({
            Action.deleted: 1,
        }, synchronize_session=False)
        db.session.query(Visit).filter(
            Visit.event_id == event.id
        ).update({
            Visit.deleted: 1,
        }, synchronize_session=False)
        db.session.query(ScheduleClientTicket).filter(
            ScheduleClientTicket.event_id == event.id
        ).update({
            ScheduleClientTicket.event_id: None,
        }, synchronize_session=False)
        db.session.query(Service).filter(
            Service.event_id == event.id
        ).update({
            Service.deleted: 1,
        }, synchronize_session=False)
        invoice_ids = [r[0] for r in db.session.query(Invoice.id.distinct()).join(
            InvoiceItem, or_(InvoiceItem.invoice_id == Invoice.id,
                             InvoiceItem.refund_id == Invoice.id)
        ).join(
            Service
        ).filter(
            Service.event_id == event.id
        )]
        if invoice_ids:
            db.session.query(Invoice).filter(
                Invoice.id.in_(invoice_ids)
            ).update({
                Invoice.deleted: 1,
            }, synchronize_session=False)
            db.session.query(InvoiceItem).filter(
                or_(InvoiceItem.invoice_id.in_(invoice_ids),
                    InvoiceItem.refund_id.in_(invoice_ids))
            ).update({
                InvoiceItem.deleted: 1,
            }, synchronize_session=False)
        db.session.commit()
        blinker.signal('Event-deleted').send(
            None,
            event_id=event_id,
            deleted_data={
                'invoices': invoice_ids
            }
        )
        return

    raise ApiException(403, msg.get('message', ''))


@module.route('/api/events.json', methods=["POST"])
@api_method
def api_get_events():
    flt = request.get_json()
    base_query = Event.query.join(Client).filter(Event.deleted == 0).options(
        db.contains_eager(Event.client),
        # db.contains_eager(Event.contract),
    )
    context = EventVisualizer()
    if 'id' in flt:
        event = base_query.filter(Event.id == flt['id']).first()
        return {
            'pages': 1,
            'items': [context.make_short_event(event)] if event else []
        }
    if 'external_id' in flt:
        base_query = base_query.filter(Event.externalId == flt['external_id'])
    if 'client_id' in flt:
        base_query = base_query.filter(Event.client_id == flt['client_id'])
    if 'beg_date_from' in flt:
        base_query = base_query.filter(Event.setDate >= safe_datetime(flt['beg_date_from']))
    if 'beg_date_to' in flt:
        base_query = base_query.filter(Event.setDate <= safe_datetime(flt['beg_date_to']))
    if 'unfinished' in flt:
        base_query = base_query.filter(Event.execDate.is_(None))
    else:
        if 'end_date_from' in flt:
            base_query = base_query.filter(Event.execDate >= safe_datetime(flt['end_date_from']))
        if 'end_date_to' in flt:
            base_query = base_query.filter(Event.execDate <= safe_datetime(flt['end_date_to']))
    if 'request_type_id' in flt:
        base_query = base_query.join(EventType).filter(EventType.requestType_id == flt['request_type_id'])
    if 'finance_id' in flt:
        base_query = base_query.join(EventType).filter(EventType.finance_id == flt['finance_id'])
    if 'speciality_id' in flt:
        base_query = base_query.outerjoin(Event.execPerson).filter(Person.speciality_id == flt['speciality_id'])
    if 'exec_person_id' in flt:
        base_query = base_query.filter(Event.execPerson_id == flt['exec_person_id'])
    if 'result_id' in flt:
        base_query = base_query.filter(Event.result_id == flt['result_id'])
    if 'org_struct_id' in flt:
        if not ('beg_date_from' in flt or 'end_date_from' in flt):
            raise ApiException(422, u'Невозможно провести поиск обращений по отделению без указания диапазона дат')
        stat_loc_query = _get_stationary_location_query(Event).with_entities(
            Event.id.label('event_id'), OrgStructure.id.label('org_struct_id')
        )
        if 'beg_date_from' in flt:
            stat_loc_query = stat_loc_query.filter(Event.setDate >= safe_datetime(flt['beg_date_from']))
        if 'beg_date_to' in flt:
            stat_loc_query = stat_loc_query.filter(Event.setDate <= safe_datetime(flt['beg_date_to']))
        if 'end_date_from' in flt:
            stat_loc_query = stat_loc_query.filter(Event.execDate >= safe_datetime(flt['end_date_from']))
        if 'end_date_to' in flt:
            stat_loc_query = stat_loc_query.filter(Event.execDate <= safe_datetime(flt['end_date_to']))
        stat_loc_query = stat_loc_query.subquery('StationaryOs')

        base_query = base_query.join(EventType).join(rbRequestType).outerjoin(
            stat_loc_query, Event.id == stat_loc_query.c.event_id
        ).filter(
            func.IF(rbRequestType.code.in_(POLICLINIC_EVENT_CODES + DIAGNOSTIC_EVENT_CODES),
                    Event.orgStructure_id == flt['org_struct_id'],
                    func.IF(rbRequestType.code.in_(STATIONARY_EVENT_CODES),
                            stat_loc_query.c.org_struct_id == flt['org_struct_id'],
                            False)
                    )
        )
    if 'diag_mkb_list' in flt:
        # latest diagnostics for *all* diagnoses
        diag_sqq = db.session.query(Diagnostic).join(
            Diagnosis
        ).filter(
            Diagnosis.deleted == 0,
            Diagnostic.deleted == 0,
        )
        diag_sqq = diag_sqq.group_by(
            Diagnostic.diagnosis_id
        )
        diag_sqq = diag_sqq.with_entities(func.max(Diagnostic.id).label('zid')).subquery()
        diag_sq = db.session.query(
            Diagnostic.id, Diagnostic.diagnosis_id,
            Diagnosis.client_id, Diagnostic.MKB.label('mkb'),
            Diagnosis.setDate.label('beg_date'),
            func.coalesce(Diagnosis.endDate, func.curdate()).label('end_date')
        ).join(
            diag_sqq, diag_sqq.c.zid == Diagnostic.id
        ).join(
            Diagnosis, Diagnostic.diagnosis_id == Diagnosis.id
        ).subquery('AllLatestDiagnostics')

        base_query = base_query.join(
            diag_sq, and_(diag_sq.c.client_id == Event.client_id,
                          diag_sq.c.beg_date <= func.coalesce(Event.execDate, func.curdate()),
                          diag_sq.c.end_date >= Event.setDate)
        ).filter(
            diag_sq.c.mkb.in_(flt['diag_mkb_list'])
        )

    if 'draft_contract' in flt:
        base_query = base_query.join(Contract).filter(Contract.draft == (flt['draft_contract'] and 1 or 0))

    order_options = flt.get('sorting_params')
    if order_options:
        desc_order = order_options['order'] == 'DESC'
        col_name = order_options['column_name']
        if col_name == 'id':
            base_query = base_query.order_by(Event.id.desc() if desc_order else Event.id)
        if col_name == 'external_id':
            # that's bad
            ext_id_order_1 = u'CAST(SUBSTR(%s, 1, 4) AS UNSIGNED)' % Event.externalId
            ext_id_order_2 = u'CAST(SUBSTR(%s, 6) AS UNSIGNED)' % Event.externalId
            if desc_order:
                ext_id_order_1 = desc(ext_id_order_1)
                ext_id_order_2 = desc(ext_id_order_2)
            base_query = base_query.order_by(ext_id_order_1, ext_id_order_2)
        elif col_name == 'type_name':
            base_query = base_query.join(EventType).order_by(EventType.name.desc() if desc_order else EventType.name)
        elif col_name == 'beg_date':
            base_query = base_query.order_by(Event.setDate.desc() if desc_order else Event.setDate)
        elif col_name == 'end_date':
            base_query = base_query.order_by(Event.execDate.desc() if desc_order else Event.execDate)
        elif col_name == 'client_full_name':
            base_query = base_query.order_by(Client.lastName.desc() if desc_order else Client.lastName)
        elif col_name == 'person_short_name':
            base_query = base_query.outerjoin(Event.execPerson).order_by(Person.lastName.desc() if desc_order else Person.lastName)
        elif col_name == 'result_text':
            base_query = base_query.outerjoin(rbResult).order_by(rbResult.name.desc() if desc_order else rbResult.name)
    else:
        base_query = base_query.order_by(Event.setDate.desc())

    per_page = int(flt.get('per_page', 20))
    page = int(flt.get('page', 1))
    paginate = base_query.paginate(page, per_page, False)
    return {
        'pages': paginate.pages,
        'total': paginate.total,
        'items': [
            context.make_short_event(event)
            for event in paginate.items
        ]
    }


@module.route('/api/event_actions/')
@module.route('/api/event_actions/<int:event_id>/<at_group>/<int:page>/<int:per_page>/')
@module.route('/api/event_actions/<int:event_id>/<at_group>/<int:page>/<int:per_page>/<order_field>/<order_type>/')
@api_method
def api_event_actions(event_id=None, at_group=None, page=None, per_page=None, order_field=None, order_type=None):
    eviz = EventVisualizer()
    event = Event.query.filter(Event.id == event_id, Event.deleted == 0).first()
    if not event:
        raise ApiException(404, u'Записи Event с id = {0} не найдено'.format(event_id))
    at_group_class = {
        'medical_documents': 0,
        'diagnostics': 1,
        'lab': 1,
        'treatments': 2
    }
    at_class = at_group_class.get(at_group)
    if at_class is None:
        raise ApiException(404, u'Неверное значение параметра \'at_group\' - {0}. Поддерживаемые значения: \'{1}\'.'.format(
            at_group,
            "', '".join(at_group_class.keys())
        ))
    if not page:
        raise ApiException(404, u'Не передан параметр \'page\'.')
    if not per_page:
        raise ApiException(404, u'Не передан параметр \'per_page\'.')
    if not order_field:
        order_field = 'beg_date'
    if not order_type:
        order_type = 'desc'
    desc_order = order_type == 'desc'

    action_query = Action.query.join(ActionType).filter(
        Action.event_id == event_id,
        Action.deleted == 0,
        ActionType.class_ == at_class
    ).options(
        joinedload(Action.actionType, innerjoin=True)
    )
    if at_group == 'lab':
        action_query = action_query.filter(ActionType.isRequiredTissue == 1)
    elif at_group == 'diagnostics':
        action_query = action_query.filter(ActionType.isRequiredTissue == 0)

    if order_field == 'at_name':
        action_query = action_query.order_by(ActionType.name.desc() if desc_order else ActionType.name)
    elif order_field == 'status_code':
        action_query = action_query.order_by(Action.status.desc() if desc_order else Action.status)
    elif order_field == 'beg_date':
        action_query = action_query.order_by(Action.begDate.desc() if desc_order else Action.begDate)
    elif order_field == 'end_date':
        action_query = action_query.order_by(Action.endDate.desc() if desc_order else Action.endDate)
    elif order_field == 'person_name':
        action_query = action_query.outerjoin(Action.person).order_by(
            Person.lastName.desc() if desc_order else Person.lastName
        )

    paginate = action_query.paginate(page, per_page, False)
    return {
        'pages': paginate.pages,
        'total': paginate.total,
        'items': [
            eviz.make_action(action) for action in paginate.items
        ]
    }
