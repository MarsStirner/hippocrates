# -*- coding: utf-8 -*-
import collections
import datetime
import itertools

from flask import request
from flask.ext.login import current_user

from nemesis.lib.apiutils import api_method
from nemesis.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_Integer, \
    ActionProperty_Date, ActionProperty_ExtReferenceRb
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.schedule import Schedule
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.card_attrs import get_card_attrs_action
from blueprints.risar.lib.represent import represent_ticket, represent_chart_short, get_pregnancy_week


__author__ = 'mmalkov'


@module.route('/api/0/schedule/')
@module.route('/api/0/schedule/<int:person_id>')
@api_method
def api_0_schedule(person_id=None):
    all_tickets = bool(request.args.get('all', False))
    if not person_id:
        person_id = safe_current_user_id()
    for_date = request.args.get('date', datetime.date.today())
    schedule_list = Schedule.query\
        .filter(Schedule.date == for_date, Schedule.person_id == person_id)\
        .order_by(Schedule.begTime).all()
    return [
        represent_ticket(ticket)
        for ticket in itertools.chain(*(schedule.tickets for schedule in schedule_list))
        if all_tickets or ticket.client_ticket
    ]


@module.route('/api/0/need_hospitalization/')
@module.route('/api/0/need_hospitalization/<int:person_id>')
@api_method
def api_0_need_hospitalization(person_id=None):
    # получение списка пациенток врача, которые нуждаются в госпитализации в стационар 2/3 уровня

    def get_delivery_date(event):
        action = get_card_attrs_action(event)
        return action['predicted_delivery_date'].value

    if not person_id:
        person_id = safe_current_user_id()

    patient_list = Event.query.join(EventType, rbRequestType, Action, ActionType, ActionProperty,
                                    ActionPropertyType, ActionProperty_Integer)\
        .filter(rbRequestType.code == 'pregnancy', Event.execDate.is_(None), Event.execPerson_id == person_id,
                ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == "prenatal_risk_572",
                ActionProperty_Integer.value_.in_([2, 3]))\
        .all()
    patient_list = filter(lambda x: get_pregnancy_week(x) >= 38, patient_list)
    patient_list.sort(key=get_delivery_date)
    return [represent_chart_short(event) for event in patient_list]


@module.route('/api/0/pregnancy_week_diagram/')
@module.route('/api/0/pregnancy_week_diagram/<int:person_id>')
@api_method
def api_0_pregnancy_week_diagram(person_id=None):
    """
    распределение пациенток на учете у врача по сроку беременности
    """
    result = [[i, 0] for i in xrange(1, 41)]
    if not person_id:
        person_id = safe_current_user_id()

    event_list = Event.query.join(EventType, rbRequestType, Action, ActionType, ActionProperty,
                                    ActionPropertyType, ActionProperty_Integer)\
        .filter(rbRequestType.code == 'pregnancy', Event.execDate.is_(None), Event.execPerson_id == person_id)\
        .all()

    for event in event_list:
        pregnancy_week = get_pregnancy_week(event)
        if pregnancy_week and pregnancy_week <= 40:
            result[pregnancy_week-1][1] += 1
    return result


@module.route('/api/0/current_stats.json')
@api_method
def api_0_current_stats():
    person_id = None
    result = collections.defaultdict(lambda: 0)
    if current_user.current_role in ('admin', 'obstetrician'):
        person_id = safe_current_user_id()

    where = [ActionType.flatCode == 'cardAttributes',
             ActionPropertyType.code == 'prenatal_risk_572',
             rbRequestType.code == 'pregnancy',
             Action.event_id == Event.id,
             ActionProperty.action_id == Action.id,
             ActionPropertyType.id == ActionProperty.type_id,
             ActionType.id == Action.actionType_id,
             ActionProperty_Integer.id == ActionProperty.id,
             Event.execDate.is_(None),
             EventType.id == Event.eventType_id,
             rbRequestType.id == EventType.requestType_id,
             Event.deleted == 0,
             Action.deleted == 0]
    if person_id:
        where.append(Event.execPerson_id == person_id)

    selectable = db.select(
        (ActionProperty_Integer.value_,),
        whereclause=db.and_(*where),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
        ))
    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result


@module.route('/api/0/death_stats.json')
@api_method
def api_0_death_stats():
    # младеньческая смертность
    result = collections.defaultdict(list)
    result1 = {'maternal_death': []}
    now = datetime.datetime.now()
    prev = now + datetime.timedelta(days=-now.day)
    selectable = db.select(
        (Action.id, ActionProperty_Integer.value_),
        whereclause=db.and_(
            ActionType.flatCode == 'risar_newborn_inspection',
            ActionPropertyType.code == 'alive',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Integer.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Integer
        ))
    for (id, value) in db.session.execute(selectable):  # 0-dead, 1-alive
        result[value].append(id)

    for value in result:
        result1[value] = []
        for i in range(1, 13):
            selectable1 = db.select(
                (Action.id,),
                whereclause=db.and_(
                    ActionType.flatCode == 'risar_newborn_inspection',
                    ActionPropertyType.code == 'date',
                    rbRequestType.code == 'pregnancy',
                    Action.event_id == Event.id,
                    ActionProperty.action_id == Action.id,
                    ActionPropertyType.id == ActionProperty.type_id,
                    ActionType.id == Action.actionType_id,
                    ActionProperty_Date.id == ActionProperty.id,
                    EventType.id == Event.eventType_id,
                    rbRequestType.id == EventType.requestType_id,
                    Event.deleted == 0,
                    Action.deleted == 0,
                    ActionProperty_Date.value.like(now.strftime('%Y')+'-'+str(i).rjust(2, '0')+'-%'),
                    Action.id.in_(result[value])
                ),
                from_obj=(
                    Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
                    ActionProperty_Date
                ))
            result1[value].append([i, db.session.execute(selectable1).rowcount])

    #материнская смертность
    def check_pat_diagnosis(action):
        pat_diagnosis = action.propsByCode['pat_diagnosis'].value
        for diag_code in ('V', 'W', 'X', 'Y'):
            if pat_diagnosis.diagnosis.mkb.DiagID.startswith(diag_code):
                return False
        return True

    for i in range(1, 13):
        actions = Action.query.join(Event, EventType, rbRequestType, Action, ActionType, ActionProperty,
                                   ActionPropertyType, ActionProperty_Date)\
            .filter(ActionType.flatCode == 'epicrisis',
                    ActionPropertyType.code == 'death_date',
                    rbRequestType.code == 'pregnancy',
                    Action.event_id == Event.id,
                    ActionProperty.action_id == Action.id,
                    ActionPropertyType.id == ActionProperty.type_id,
                    ActionType.id == Action.actionType_id,
                    ActionProperty_Date.id == ActionProperty.id,
                    EventType.id == Event.eventType_id,
                    rbRequestType.id == EventType.requestType_id,
                    Event.deleted == 0,
                    Action.deleted == 0,
                    ActionProperty_Date.value.like(now.strftime('%Y')+'-'+str(i).rjust(2, '0')+'-%')
                    ).all()
        actions = filter(check_pat_diagnosis, actions)
        result1['maternal_death'].append([i, len(actions)])
    return result1


@module.route('/api/0/pregnancy_final_stats.json')
@api_method
def api_0_pregnancy_final_stats():
    now = datetime.datetime.now()
    finished_cases = []
    result = collections.defaultdict(lambda: 0)
    selectable = db.select(
        (Action.id, ),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'delivery_date',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Date.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            ActionProperty_Date.value.like(now.strftime('%Y')+'-%')
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Date
        ))
    for (id, ) in db.session.execute(selectable):
        finished_cases.append(id)

    selectable = db.select(
        (ActionProperty_ExtReferenceRb.value_, ),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'pregnancy_final',
            rbRequestType.code == 'pregnancy',
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_ExtReferenceRb.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            Action.id.in_(finished_cases)
        ),
        from_obj=(
            Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_ExtReferenceRb
        ))
    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result