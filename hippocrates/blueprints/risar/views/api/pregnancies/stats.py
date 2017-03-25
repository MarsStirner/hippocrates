# -*- coding: utf-8 -*-
import collections
import datetime
import time

from flask import request
from sqlalchemy import func

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_fill_rate import CFRController
from hippocrates.blueprints.risar.lib.org_bcl import OrgBirthCareLevelRepr, OrganisationRepr, EventRepr
from hippocrates.blueprints.risar.lib.pregnancy_dates import get_pregnancy_week
from hippocrates.blueprints.risar.lib.represent.errand import represent_errand
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_chart_short
from hippocrates.blueprints.risar.lib.stats import StatsController, get_infant_death_coefficient, \
    get_maternal_coefficient, get_children_stat, get_maternal_death, \
    get_list_of_alive_dead_actions, get_children_cards_info
from hippocrates.blueprints.risar.risar_config import checkup_flat_codes, request_type_pregnancy

from nemesis.app import app
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_int, safe_unicode, safe_datetime, safe_date
from nemesis.lib.vesta import Vesta
from nemesis.models.actions import ActionType, Action, ActionProperty, ActionPropertyType, ActionProperty_Integer, \
    ActionProperty_Date, ActionProperty_ExtReferenceRb
from nemesis.models.event import Event, EventType
from nemesis.models.client import Client
from nemesis.models.exists import rbRequestType
from nemesis.models.organisation import Organisation, OrganisationCurationAssoc
from nemesis.models.person import Person, PersonCurationAssoc, rbOrgCurationLevel
from nemesis.models.risar import TerritorialRate, rbRateType, Errand, rbErrandStatus
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


def get_rate_for_regions(regions, rate_code):
    rate = {}
    for region in regions:
        result = []
        selectable = db.select(
            (TerritorialRate.year, TerritorialRate.value),
            whereclause=db.and_(
                TerritorialRate.kladr_code == region,
                rbRateType.id == TerritorialRate.rate_type_id,
                rbRateType.code == rate_code
            ),
            from_obj=(
                TerritorialRate, rbRateType
            ))
        for (year, value) in db.session.execute(selectable):
            result.append([year, value])
        if result:
            if region == '00000000000':
                rate[u'РФ'] = result
            else:
                region_info = Vesta.search_kladr_locality(region, 1)[0]
                rate[region_info.fullname] = result
    return rate


@module.route('/api/0/stats/current_cards_overview/')
@api_method
def api_0_stats_current_cards_overview():
    def two_months(event):
        now = datetime.datetime.now()
        checkups = Action.query.join(ActionType).filter(
            Action.event == event,
            Action.deleted == 0,
            ActionType.flatCode.in_(checkup_flat_codes)
        ).order_by(Action.begDate).all()
        if checkups:
            return True if (now - checkups[-1].begDate).days / 60. > 2 else False
        else:
            return True if (now - event.setDate).days / 60. > 2 else False

    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')

    query = Event.query.join(EventType, rbRequestType, Action, ActionType, ActionProperty,
                             ActionPropertyType, ActionProperty_Integer) \
        .filter(rbRequestType.code == request_type_pregnancy, Event.deleted == 0, Event.execDate.is_(None))

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
    events_undefined_risk = len(
        filter(lambda x: PregnancyCard.get_for_event(x).attrs['prenatal_risk_572'].value.code == 'undefined',
               event_list))
    return {
        'events_all': events_all,
        'events_45': events_45,
        'events_2_months': events_2_months,
        'events_undefined_risk': events_undefined_risk
    }


@module.route('/api/1/stats/current_cards_overview/')
@module.route('/api/1/stats/current_cards_overview/<int:person_id>')
@api_method
def api_1_stats_current_cards_overview(person_id=None):
    if not person_id:
        person_id = safe_current_user_id()
    args = request.args.to_dict()
    curation_level = safe_unicode(args.get('curation_level_code'))

    stats_ctrl = StatsController()
    data = stats_ctrl.get_current_cards_overview(person_id, curation_level)
    return data


@module.route('/api/0/recent_charts.json')
@api_method
def api_0_recent_charts():
    person_id = safe_current_user_id()
    boundary_date = datetime.datetime.now() - datetime.timedelta(days=7)
    curation_level = request.args.get('curation_level')

    query = Event.query.join(EventType, rbRequestType, Client) \
        .filter(rbRequestType.code == request_type_pregnancy, Event.deleted == 0, Event.execDate.is_(None),
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
        'events': [represent_pregnancy_chart_short(event) for event in pagination.items]}


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

    query = Event.query.join(EventType, rbRequestType, Client, Action, ActionType,
                             ActionProperty, ActionPropertyType,
                             ActionProperty_Integer) \
        .filter(rbRequestType.code == request_type_pregnancy, Event.deleted == 0, Event.execDate.is_(None),
                Action.deleted == 0, ActionProperty.deleted == 0,
                ActionType.flatCode == 'cardAttributes', ActionPropertyType.code == "prenatal_risk_572",
                ActionProperty_Integer.value_.in_(risk_rate))
    if curation_level:
        query = query.join(Organisation, OrganisationCurationAssoc, PersonCurationAssoc, rbOrgCurationLevel)
        query = query.filter(PersonCurationAssoc.person_id == person_id,
                             rbOrgCurationLevel.code == curation_level)
    elif person_id:
        query = query.filter(Event.execPerson_id == person_id)

    per_page = safe_int(j.get('per_page', 5))
    page = safe_int(j.get('page', 1))
    pagination = query.order_by(Event.setDate.desc()).paginate(page, per_page)
    events = [represent_pregnancy_chart_short(event) for event in pagination.items]
    events.sort(key=lambda x: x['modify_date'], reverse=True)
    return {
        'count': pagination.total,
        'total_pages': pagination.pages,
        'events': events}


@module.route('/api/0/need_hospitalization/')
@module.route('/api/0/need_hospitalization/<int:person_id>')
@api_method
def api_0_need_hospitalization(person_id=None):
    """получение списка пациенток врача, которые нуждаются в госпитализации в стационар 2/3 уровня"""
    if not person_id:
        person_id = safe_current_user_id()

    stats_ctrl = StatsController()
    events = stats_ctrl.get_cards_urgent_hosp(person_id)
    return [
        represent_pregnancy_chart_short(event) for event in events
        ]


@module.route('/api/0/stats/pregnancy_week_diagram/')
@module.route('/api/0/stats/pregnancy_week_diagram/<int:person_id>')
@api_method
def api_0_stats_pregnancy_week_diagram(person_id=None):
    """
    распределение пациенток на учете у врача по сроку беременности
    """
    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')
    result = [[i, 0] for i in xrange(1, 41)]
    result.append(['40+', 0])

    query = Event.query.join(EventType, rbRequestType) \
        .filter(rbRequestType.code == request_type_pregnancy, Event.deleted == 0, Event.execDate.is_(None))

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
            result[pregnancy_week - 1][1] += 1
        elif pregnancy_week and pregnancy_week > 40:
            result[40][1] += 1
    return result


@module.route('/api/1/stats/pregnancy_week_diagram/')
@module.route('/api/1/stats/pregnancy_week_diagram/<int:person_id>')
@api_method
def api_1_stats_pregnancy_week_diagram(person_id=None):
    if not person_id:
        person_id = safe_current_user_id()
    args = request.args.to_dict()
    curation_level = safe_unicode(args.get('curation_level_code'))

    stats_ctrl = StatsController()
    data = stats_ctrl.get_cards_pregnancy_week_distribution(person_id, curation_level)
    return data


@module.route('/api/0/stats/radz_risk_rate/')
@module.route('/api/0/stats/radz_risk_rate/<int:person_id>')
@api_method
def api_0_stats_radz_risks(person_id=None):
    person_id = person_id or safe_current_user_id()
    curation_level = request.args.get('curation_level_code')
    stats_ctrl = StatsController()
    data = stats_ctrl.get_radz_risks(person_id, curation_level)
    return data


@module.route('/api/0/stats/regional_risk_rate/')
@module.route('/api/0/stats/regional_risk_rate/<int:person_id>')
@api_method
def api_0_stats_regional_risks(person_id=None):
    person_id = person_id or safe_current_user_id()
    curation_level = request.args.get('curation_level_code')
    stats_ctrl = StatsController()
    data = stats_ctrl.get_regional_risks(person_id, curation_level)
    return data


@module.route('/api/0/stats/risk_group_distribution/')
@module.route('/api/0/stats/risk_group_distribution/<int:person_id>')
@api_method
def api_0_stats_risk_group_distribution(person_id=None):
    person_id = person_id or safe_current_user_id()
    curation_level = request.args.get('curation_level_code')

    stats_ctrl = StatsController()
    data = stats_ctrl.get_risk_groups_distribution(person_id, curation_level)
    return data


@module.route('/api/0/stats/perinatal_risk_rate.json')
@api_method
def api_0_stats_perinatal_risk_rate():
    person_id = safe_current_user_id()
    curation_level = request.args.get('curation_level')
    result = collections.defaultdict(lambda: 0)

    where = [ActionType.flatCode == 'cardAttributes',
             ActionPropertyType.code == 'prenatal_risk_572',
             rbRequestType.code == request_type_pregnancy,
             ActionProperty.action_id == Action.id,
             ActionPropertyType.id == ActionProperty.type_id,
             ActionType.id == Action.actionType_id,
             Event.execDate.is_(None),
             EventType.id == Event.eventType_id,
             rbRequestType.id == EventType.requestType_id,
             Event.deleted == 0,
             Action.deleted == 0]
    from_obj = Event.__table__.join(EventType).join(rbRequestType).join(Client).join(
        Person, Event.execPerson_id == Person.id
    ).join(
        Action, Action.event_id == Event.id
    ).join(ActionType) \
        .join(ActionProperty).join(ActionPropertyType).outerjoin(ActionProperty_Integer)

    if curation_level:
        from_obj.join(
            Organisation, Person.org_id == Organisation.id
        ).join(OrganisationCurationAssoc).join(PersonCurationAssoc).join(rbOrgCurationLevel)
        where.extend([
            Person.org_id == Organisation.id,
            OrganisationCurationAssoc.org_id == Organisation.id,
            OrganisationCurationAssoc.personCuration_id == PersonCurationAssoc.id,
            PersonCurationAssoc.person_id == person_id,
            PersonCurationAssoc.orgCurationLevel_id == rbOrgCurationLevel.id,
            rbOrgCurationLevel.code == curation_level
        ])
    elif person_id:
        where.append(Event.execPerson_id == person_id)

    selectable = db.select(
        (ActionProperty_Integer.value_,),
        whereclause=db.and_(*where),
        from_obj=from_obj)
    for (value,) in db.session.execute(selectable):
        if value:
            result[value] += 1
        else:
            result[0] += 1
    return result


def get_dates_and_ranges():
    start_date, end_date = safe_datetime(safe_date(request.args.get('start_date'))), safe_datetime(
        safe_date(request.args.get('end_date')))
    end_date = end_date or datetime.datetime.now()
    start_date = start_date or end_date - datetime.timedelta(days=1)
    days = (end_date - start_date).days
    dt_range = [(start_date + datetime.timedelta(days=x)).date() for x in range(0, days + 1)]
    dt_range = []
    timestamped_dt_range = []
    for x in range(0, days + 1):
        idate = (start_date + datetime.timedelta(days=x)).date()
        dt_range.append(idate)
        timestamped_dt_range.append(time.mktime(idate.timetuple()))
    return start_date, end_date, dt_range, timestamped_dt_range


@module.route('/api/0/maternal_death_stats.json')
@api_method
def api_0_maternal_death_stats():
    # перинатальная смертности и материнская смертность
    regions = ['00000000000']
    regions.extend(app.config.get('RISAR_REGIONS', []))

    start_date, end_date, dt_range, timestamped_dt_range = get_dates_and_ranges()
    maternal_death = get_maternal_death(start_date, end_date)

    chart_data = {'maternal_death': [],
                  'maternal_cards_info': [],
                  }

    for i, dt in enumerate(dt_range, 1):
        chart_data['maternal_death'].append([i, maternal_death.get(dt, {}).get('length', 0)])
        chart_data['maternal_cards_info'].append(maternal_death.get(dt, {}).get('cards', []))

    return {
        'dt_range': timestamped_dt_range,
        'maternal_death': chart_data['maternal_death'],
        'maternal_death_coeff': get_maternal_coefficient(start_date, end_date),
        'maternal_cards_info': chart_data['maternal_cards_info'],
        "prev_years_maternal_death": get_rate_for_regions(regions, "maternal_death"),
    }

@module.route('/api/0/perinatal_death_stats.json')
@api_method
def api_0_perinatal_death_stats():
    # перинатальная смертности и материнская смертность
    regions = ['00000000000']
    regions.extend(app.config.get('RISAR_REGIONS', []))

    start_date, end_date, dt_range, timestamped_dt_range = get_dates_and_ranges()

    dict_of_children_ids = get_list_of_alive_dead_actions(start_date, end_date)
    dead_children = get_children_stat(children_ids=dict_of_children_ids.get(0, []))
    alive_children = get_children_stat(children_ids=dict_of_children_ids.get(1, []))

    alive_children_cards_info = get_children_cards_info(dict_of_children_ids.get(1, {}))
    dead_children_cards_info = get_children_cards_info(dict_of_children_ids.get(0, {}))
    from pprint import pprint
    pprint(alive_children_cards_info)
    chart_data = {
        'dead_children': [],
        'alive_children': [],
        'dead_children_cards_info': [],
        'alive_children_cards_info': []
    }

    for i, dt in enumerate(dt_range, 1):
        chart_data['dead_children'].append([i, dead_children.get(dt, 0)])
        chart_data['alive_children'].append([i, alive_children.get(dt, 0)])
        chart_data['dead_children_cards_info'].append(dead_children_cards_info.get(dt, []))
        chart_data['alive_children_cards_info'].append(alive_children_cards_info.get(dt, []))

    return {
        'dt_range': timestamped_dt_range,
        "infants_death_coeff": get_infant_death_coefficient(start_date, end_date),
        "dead_children": chart_data['dead_children'],
        "dead_children_cards_info": chart_data['dead_children_cards_info'],
        "alive_children": chart_data['alive_children'],
        "alive_children_cards_info": chart_data['alive_children_cards_info'],
        "prev_years_perinatal_death": get_rate_for_regions(regions, "perinatal_death"),
        "prev_years_birth": get_rate_for_regions(regions, "birth"),
    }


@module.route('/api/0/pregnancy_final_stats.json')
@api_method
def api_0_pregnancy_final_stats():
    now = datetime.datetime.now()
    finished_cases = []
    result = collections.defaultdict(lambda: 0)
    selectable = db.select(
        (Action.id,),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'delivery_date',
            rbRequestType.code == request_type_pregnancy,
            Action.event_id == Event.id,
            ActionProperty.action_id == Action.id,
            ActionPropertyType.id == ActionProperty.type_id,
            ActionType.id == Action.actionType_id,
            ActionProperty_Date.id == ActionProperty.id,
            EventType.id == Event.eventType_id,
            rbRequestType.id == EventType.requestType_id,
            Event.deleted == 0,
            Action.deleted == 0,
            func.year(ActionProperty_Date.value) == now.strftime('%Y')
        ),
        from_obj=(
            Event, EventType, rbRequestType, Client, Action, ActionType, ActionProperty, ActionPropertyType,
            ActionProperty_Date
        ))
    for (id,) in db.session.execute(selectable):
        finished_cases.append(id)

    selectable = db.select(
        (ActionProperty_ExtReferenceRb.value_,),
        whereclause=db.and_(
            ActionType.flatCode == 'epicrisis',
            ActionPropertyType.code == 'pregnancy_final',
            rbRequestType.code == request_type_pregnancy,
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
    for (value,) in db.session.execute(selectable):
        result[value] += 1
    return result


@module.route('/api/0/stats/org_birth_care_level/')
@api_method
def api_0_stats_obcl_get():
    return OrgBirthCareLevelRepr().represent_levels()


@module.route('/api/0/stats/org_birth_care_level/orgs_info/')
@module.route('/api/0/stats/org_birth_care_level/orgs_info/<int:obcl_id>')
@api_method
def api_0_stats_obcl_orgs_get(obcl_id=None):
    return OrgBirthCareLevelRepr().represent_level_orgs(obcl_id)


@module.route('/api/0/stats/org_curation/')
@api_method
def api_0_stats_org_curation_get():
    return OrganisationRepr().represent_curations()


@module.route('/api/0/stats/pregnancy_pathology/')
@api_method
def api_0_stats_pregnancy_pathology():
    person_id = safe_current_user_id()
    curation_level_code = request.args.get('curation_level_code')
    return EventRepr().represent_by_pregnancy_pathology(person_id, curation_level_code)


@module.route('/api/0/stats/urgent_errands/')
@api_method
def api_0_stats_urgent_errands():
    person_id = safe_current_user_id()
    errands = Errand.query.join(rbErrandStatus, Event, Client,
                                Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_Integer) \
        .filter(Errand.execPerson_id == person_id, rbErrandStatus.code.in_(['waiting', 'expired']),
                ActionType.flatCode == 'cardAttributes',
                ActionPropertyType.code == "prenatal_risk_572", ActionProperty.deleted == 0, ) \
        .order_by(func.date(Errand.plannedExecDate)).order_by(ActionProperty_Integer.value_.desc()).limit(10).all()
    return [represent_errand(errand) for errand in errands]


@module.route('/api/0/stats/card_fill_rates/doctor/')
@module.route('/api/0/stats/card_fill_rates/doctor/<int:doctor_id>')
@api_method
def api_0_stats_doctor_card_fill_rates(doctor_id=None):
    if not doctor_id:
        doctor_id = safe_current_user_id()
    cfr_ctrl = CFRController()
    data = cfr_ctrl.get_doctor_card_fill_rates(doctor_id)
    return data


@module.route('/api/0/stats/card_fill_rates/lpu_overview/')
@module.route('/api/0/stats/card_fill_rates/lpu_overview/<int:curator_id>')
@api_method
def api_0_stats_card_fill_rates_lpu_overview(curator_id=None):
    if not curator_id:
        curator_id = safe_current_user_id()
    cfr_ctrl = CFRController()
    data = cfr_ctrl.get_card_fill_rates_lpu_overview(curator_id)
    return data


@module.route('/api/0/stats/card_fill_rates/doctor_overview/')
@module.route('/api/0/stats/card_fill_rates/doctor_overview/<int:curator_id>')
@api_method
def api_0_stats_card_fill_rates_doctor_overview(curator_id=None):
    if not curator_id:
        curator_id = safe_current_user_id()
    args = request.args.to_dict()
    if 'curation_level_code' not in args:
        raise ApiException(404, u'необходим `curation_level_code`')
    curation_level = safe_unicode(args.get('curation_level_code'))

    cfr_ctrl = CFRController()
    data = cfr_ctrl.get_card_fill_rates_doctor_overview(curator_id, curation_level)
    return data


@module.route('/api/0/stats/controlled_events/')
@module.route('/api/0/stats/controlled_events/<int:person_id>')
@api_method
def api_0_stats_controlled_events(person_id=None):
    if not person_id:
        person_id = safe_current_user_id()
    args = request.args.to_dict()
    curation_level = safe_unicode(args.get('curation_level_code'))

    stats_ctrl = StatsController()
    data = stats_ctrl.get_controlled_events(person_id, curation_level)
    return data
