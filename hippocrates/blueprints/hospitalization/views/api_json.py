# -*- coding: utf-8 -*-
import json

from flask import request, render_template
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import join
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager, aliased

from hippocrates.blueprints.event.lib.utils import MovingController
from hippocrates.blueprints.hospitalization.lib.utils import get_hospitalization_info
from nemesis.lib.apiutils import api_method
from nemesis.lib.const import STATIONARY_MOVING_CODE, STATIONARY_EVENT_CODES, STATIONARY_ORG_STRUCT_STAY_CODE, \
    STATIONARY_HOSP_BED_CODE, STATIONARY_HOSP_LENGTH_CODE
from nemesis.lib.data import get_hosp_length
from nemesis.lib.diagnosis import get_events_diagnoses
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType, ActionProperty_OrgStructure, \
    ActionProperty_HospitalBed, OrgStructure_HospitalBed, ActionProperty_Integer
from nemesis.models.client import Client
from nemesis.models.enums import HospitalizationStageStatus
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType, OrgStructure
from nemesis.systemwide import db
from ..app import module


@module.route('/index.html')
def index():
    return render_template('hospitalization/base.html')


@module.route('/api/get_data')
@api_method
def get_data():
    kwargs = request.args.to_dict()
    hosp_info = get_hosp_info(**kwargs)
    result = {'hospitalizations': []}
    diag_ids = []
    for info in hosp_info:
        result['hospitalizations'].append(get_hospitalization_info(info))
        diag_ids.append(info.Event.id)

    diags = get_events_diagnoses(diag_ids)
    for i in result['hospitalizations']:
        diag = diags.get(i['id'])
        i['diagnosis'] = diag or {}
    return result


def get_hosp_info(**kwargs):
    begDT = kwargs['startDateTime']
    endDT = kwargs['endDateTime']

    base_query = db.session.query(Event).join(Client, EventType, rbRequestType).filter(Event.deleted == 0)
    if 'startDateTime' in kwargs:
        base_query = base_query.filter(or_(Event.execDate >= kwargs['startDateTime'], Event.execDate.is_(None)))
    if 'endDateTime' in kwargs:
        base_query = base_query.filter(Event.setDate <= kwargs['endDateTime'])
    if 'externalId' in kwargs:
        base_query = base_query.filter(Event.externalId == kwargs['externalId'])
    if 'clientId' in kwargs:
        base_query = base_query.filter(Event.client_id == kwargs['clientId'])
    if 'execPersonId' in kwargs:
        base_query = base_query.filter(Event.execPerson_id == kwargs['execPersonId'])

    # if 'clientStatus' in kwargs:
    c_status = int(kwargs.get('clientStatus', -1))
    if c_status == HospitalizationStageStatus.getId('current'):
        base_query = base_query.filter(and_(
            Event.setDate <= kwargs['startDateTime'],
            or_(Event.execDate >= kwargs['endDateTime'], Event.execDate.is_(None)))
        )
    # elif c_status == HospitalizationStageStatus.getId('received'):
    #     base_query = base_query.filter(and_(
    #         Event.setDate >= kwargs['startDateTime'],
    #         Event.setDate <= kwargs['endDateTime'])
    #     )
    elif c_status == HospitalizationStageStatus.getId('discharged'):
        base_query = base_query.filter(and_(
            Event.execDate >= kwargs['startDateTime'],
            Event.execDate <= kwargs['endDateTime'])
        )

    # самая поздняя дата движения для каждого обращения пациента
    q_action_begdates = db.session.query(Action).join(
        Event, EventType, rbRequestType, ActionType,
    ).filter(
        Event.deleted == 0, Action.deleted == 0, rbRequestType.code.in_(STATIONARY_EVENT_CODES),
        ActionType.flatCode == STATIONARY_MOVING_CODE
    ).with_entities(
        func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
    ).group_by(
        Event.id
    ).subquery('MaxActionBegDates')

    # самое позднее движение (включая уже и дату и id, если даты совпадают) для каждого обращения пациента
    q_latest_movings_ids = db.session.query(Action).join(
        q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                q_action_begdates.c.event_id == Action.event_id)
    ).with_entities(
        func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
    ).group_by(
        Action.event_id
    ).subquery('EventLatestMovings')

# """
# LEFT JOIN ActionProperty_Double appendages_right_increased ON appendages_right_increased.id= (
#   SELECT _ap.id
#   FROM ActionProperty _ap
#   INNER JOIN ActionPropertyType _apt ON _apt.id = _ap.type_id AND _apt.code = 'appendages_right_increased'
#   WHERE _ap.deleted = 0
#   AND _apt.deleted = 0
#   AND _ap.action_id = a.id
#   LIMIT 1
# )
# """

    MovingAction = aliased(Action, name='MovingAction')

    q_os_stay_sq = db.session.query(ActionProperty.id.label('ap_id'))\
        .join(ActionPropertyType)\
        .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                ActionProperty.action_id == MovingAction.id)\
        .limit(1)

    q_hosp_bed = db.session.query(ActionProperty.id.label('ap_id'))\
        .join(ActionPropertyType)\
        .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                ActionPropertyType.code == STATIONARY_HOSP_BED_CODE,
                ActionProperty.action_id == MovingAction.id)\
        .limit(1)

    # .join(ActionProperty_HospitalBed, xxx.ap_id == ActionProperty_OrgStructure.id) \

    q_latest_movings = db.session.query(MovingAction)\
        .join(q_latest_movings_ids, MovingAction.id == q_latest_movings_ids.c.action_id) \
        .join(ActionProperty_OrgStructure, ActionProperty_OrgStructure.id == q_os_stay_sq) \
        .join(OrgStructure, OrgStructure.id == ActionProperty_OrgStructure.value_) \
        .outerjoin(ActionProperty_HospitalBed, ActionProperty_HospitalBed.id == q_hosp_bed) \
        .outerjoin(OrgStructure_HospitalBed, OrgStructure_HospitalBed.id == ActionProperty_HospitalBed.value_)\
        .with_entities(MovingAction.id.label('action_id'), MovingAction.event_id.label('event_id'),
                       OrgStructure.id.label('os_stay_id'), OrgStructure.name.label('os_stay_name'),
                       OrgStructure_HospitalBed.idx.label('os_hosp_bed'),
                       MovingAction.begDate.label('begDate'), MovingAction.endDate.label('endDate'))
    if 'orgStructId' in kwargs:
        q_latest_movings = q_latest_movings.filter(OrgStructure.id == kwargs['orgStructId'])
    q_latest_movings = q_latest_movings.subquery('q_latest_movings')

    base_query = base_query.outerjoin(q_latest_movings, Event.id == q_latest_movings.c.event_id)\
        .with_entities(Event, Client, q_latest_movings.c.id, q_latest_movings.c.os_stay_name, q_latest_movings.c.os_hosp_bed,
                       q_latest_movings.c.begDate, q_latest_movings.c.endDate)\
        .options(contains_eager(Event.client))

    if c_status == HospitalizationStageStatus.getId('received'):
        base_query = base_query.filter(q_latest_movings.c.begDate >= begDT, q_latest_movings.c.begDate < endDT)
    if c_status == HospitalizationStageStatus.getId('transferred'):
        base_query = base_query.filter(q_latest_movings.c.endDate >= begDT, q_latest_movings.c.endDate < endDT)
    if 'orgStructId' in kwargs:
        base_query = base_query.filter(q_latest_movings.c.event_id.isnot(None))

    data = base_query.all()
    return data


