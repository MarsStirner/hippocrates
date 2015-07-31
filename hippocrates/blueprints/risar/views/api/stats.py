# -*- coding: utf-8 -*-
import collections
import datetime

from flask import request

from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_int
from nemesis.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_Integer, \
    ActionProperty_Date, ActionProperty_ExtReferenceRb
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.models.organisation import Organisation, OrganisationCurationAssoc
from nemesis.models.person import PersonCurationAssoc, rbOrgCurationLevel
from nemesis.models.utils import safe_current_user_id
from nemesis.models.risar import TerritorialRate, rbRateType
from nemesis.systemwide import db
from blueprints.risar.app import module
from blueprints.risar.lib.card_attrs import get_card_attrs_action
from blueprints.risar.lib.represent import represent_ticket, represent_chart_short, get_pregnancy_week
from blueprints.risar.risar_config import checkup_flat_codes


@module.route('/api/0/current_stats.json')
@api_method
def api_0_current_stats():
    def two_months(event):
        now = datetime.datetime.now()
        checkups = Action.query.join(ActionType).filter(
            Action.event == event,
            Action.deleted == 0,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).order_by(Action.begDate).all()
        if checkups:
            return True if (now - checkups[-1].begDate).days/60. > 2 else False
        else:
            return True if (now - event.setDate).days/60. > 2 else False

    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')

    query = Event.query.join(EventType, rbRequestType, Action, ActionType, ActionProperty,
                                    ActionPropertyType, ActionProperty_Integer)\
        .filter(rbRequestType.code == 'pregnancy', Event.deleted == 0, Event.execDate.is_(None))

    if curation_level:
        query = query.join(Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel)
        query = query.filter(Event.org_id == Organisation.id, OrganisationCurationAssoc.org_id == Organisation.id,
                             OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id,
                             PersonCurationAssoc.person_id == person_id,
                             PersonCurationAssoc.orgCurationLevel_id == rbOrgCurationLevel.id,
                             rbOrgCurationLevel.code == curation_level)
    elif person_id:
        query = query.filter(Event.execPerson_id == person_id)

    event_list = query.all()

    events_all = len(event_list)
    events_45 = len(filter(lambda x: get_pregnancy_week(x) >= 45, event_list))
    events_2_months = len(filter(lambda x: two_months(x), event_list))
    events_undefined_risk = len(filter(lambda x: get_card_attrs_action(x)['prenatal_risk_572'].value == 0, event_list))
    return {
        'events_all': events_all,
        'events_45': events_45,
        'events_2_months': events_2_months,
        'events_undefined_risk': events_undefined_risk
    }


@module.route('/api/0/recent_charts.json')
@api_method
def api_0_recent_charts():
    person_id = safe_current_user_id()
    boundary_date = datetime.datetime.now() - datetime.timedelta(days=7)
    curation_level = request.args.get('curation_level')

    query = Event.query.join(EventType, rbRequestType)\
        .filter(rbRequestType.code == 'pregnancy', Event.deleted == 0, Event.execDate.is_(None),
                Event.setDate >= boundary_date)

    if curation_level:
        query = query.join(Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel)
        query = query.filter(PersonCurationAssoc.person_id == person_id,
                             rbOrgCurationLevel.code == curation_level)
    elif person_id:
        query = query.filter(Event.execPerson_id == person_id)

    per_page = safe_int(request.args.get('per_page', 5))
    page = safe_int(request.args.get('page', 1))
    pagination = query.order_by(Event.setDate.desc()).paginate(page, per_page)
    return {
        'count': pagination.total,
        'total_pages': pagination.pages,
        'events': [represent_chart_short(event) for event in pagination.items]}


@module.route('/api/0/recently_modified_charts.json', methods=['POST'])
@api_method
def api_0_recently_modified_charts():
    """
    карты пациенток со степенью риска выше низкой, отсортированные по дате последнего изменения
    """
    j = request.get_json()
    person_id = safe_current_user_id()
    curation_level = j.get('curation_level')
    risk_rate = j.get('risk_rate')

    query = Event.query.join(EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType,
                             ActionProperty_Integer)\
        .filter(rbRequestType.code == 'pregnancy', Event.deleted == 0, Event.execDate.is_(None),
                ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == "prenatal_risk_572",
                ActionProperty_Integer.value_.in_(risk_rate))

    if curation_level:
        query = query.join(Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel)
        query = query.filter(PersonCurationAssoc.person_id == person_id,
                             rbOrgCurationLevel.code == curation_level)
    elif person_id:
        query = query.filter(Event.execPerson_id == person_id)

    per_page = safe_int(request.args.get('per_page', 5))
    page = safe_int(request.args.get('page', 1))
    pagination = query.order_by(Event.setDate.desc()).paginate(page, per_page)
    events = [represent_chart_short(event) for event in pagination.items]
    events.sort(key=lambda x: x['modify_date'], reverse=True)
    return {
        'count': pagination.total,
        'total_pages': pagination.pages,
        'events': events}


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
        .filter(rbRequestType.code == 'pregnancy', Event.deleted == 0, Event.execDate.is_(None), Event.execPerson_id == person_id,
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
    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')
    result = [[i, 0] for i in xrange(1, 41)]
    result.append(['40+', 0])

    query = Event.query.join(EventType, rbRequestType)\
        .filter(rbRequestType.code == 'pregnancy', Event.deleted == 0, Event.execDate.is_(None))

    if curation_level:
        query = query.join(Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel)
        query = query.filter(PersonCurationAssoc.person_id == person_id,
                             rbOrgCurationLevel.code == curation_level)
    elif person_id:
        query = query.filter(Event.execPerson_id == person_id)

    event_list = query.all()

    for event in event_list:
        pregnancy_week = get_pregnancy_week(event)
        if pregnancy_week and pregnancy_week <= 40:
            result[pregnancy_week-1][1] += 1
        elif pregnancy_week and pregnancy_week > 40:
            result[40][1] += 1
    return result


@module.route('/api/0/prenatal_risk_stats.json')
@api_method
def api_0_prenatal_risk_stats():
    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')
    result = collections.defaultdict(lambda: 0)

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
    from_obj = [
        Event, EventType, rbRequestType, Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer
    ]

    if curation_level:
        from_obj.extend([Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel])
        where.extend([Event.org_id == Organisation.id, OrganisationCurationAssoc.org_id == Organisation.id,
                      OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id,
                      PersonCurationAssoc.person_id == person_id,
                      PersonCurationAssoc.orgCurationLevel_id == rbOrgCurationLevel.id, rbOrgCurationLevel.code == curation_level])
    elif person_id:
        where.append(Event.execPerson_id == person_id)

    selectable = db.select(
        (ActionProperty_Integer.value_,),
        whereclause=db.and_(*where),
        from_obj=from_obj)
    for (value, ) in db.session.execute(selectable):
        result[value] += 1
    return result


@module.route('/api/0/death_stats.json')
@api_method
def api_0_death_stats():
    #перинатальная смертности и материнская смертность
    regions = ['00000000000']
    regions.extend(app.config.get('RISAR_REGIONS', []))

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

    perinatal_death_rate = {}
    for region in regions:
        perinatal_death_rate[region] = []
        selectable = db.select(
            (TerritorialRate.year, TerritorialRate.value),
            whereclause=db.and_(
                TerritorialRate.kladr_code == region,
                rbRateType.code == "perinatal_death",
                rbRequestType.code == 'pregnancy'
            ),
            from_obj=(
                TerritorialRate, rbRateType
            ))
        for (year, value) in db.session.execute(selectable):  #
            perinatal_death_rate[region].append([year, value])

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
    return result1, perinatal_death_rate


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
