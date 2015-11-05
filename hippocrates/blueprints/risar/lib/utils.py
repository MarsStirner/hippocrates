# -*- coding: utf-8 -*-

import datetime
from sqlalchemy.orm import lazyload

from nemesis.lib.data import create_action, update_action
from nemesis.lib.utils import safe_traverse_attrs, safe_dict, safe_traverse, safe_datetime
from nemesis.models.actions import Action, ActionType, ActionProperty, ActionPropertyType
from nemesis.models.event import Event, Diagnostic, Diagnosis
from nemesis.models.risar import rbPregnancyPathology, rbPerinatalRiskRate
from nemesis.models.enums import ActionStatus
from nemesis.models.exists import MKB
from nemesis.models.person import Person
from nemesis.systemwide import cache, db
from blueprints.risar.risar_config import checkup_flat_codes, first_inspection_code, inspection_preg_week_code


risk_rates_diagID = {
    'low': ['Z34.0', 'Z34.8', 'Z34.9'],
    'middle': ['I34.1', 'О99.5', 'E04.0', 'E04.1', 'E04.2', 'E04.3', 'E04.4', 'E04.5', 'E04.6', 'E04.7', 'E04.8',
               'E04.9', 'Н52.1', 'N11.0', 'N11.1', 'N11.2', 'N11.3', 'N11.4', 'N11.5', 'N11.6', 'N11.7', 'N11.8',
               'N11.9', 'N30.1', 'N30.2', 'K29.3', 'K29.4', 'K29.5', 'K29.8', 'K29.9', 'K51.0', 'K51.1', 'K51.2',
               'K51.3', 'O48', 'O36.6', 'O33.5', 'O33.0',
               'O33.1', 'O33.2', 'O33.3', 'O32.1', 'O44.0', 'Z35.2', 'O30.0', 'O30.1', 'O30.2', 'O30.8', 'O30.9',
               'О34.2', 'O34.2', 'Z35.0', 'O40', 'О42', 'O47.0', 'O60', 'О36.5', 'P05'],
    'high': ['O42', 'O47.0', 'O44', 'O44.0', 'O36.2', 'O14.0', 'O14.1', 'O14.9', 'O11', 'O12', 'O15.0', 'O15.1',
             'O15.9', 'O26.6', 'O34.2',
             'O34.6', 'O34.7', 'O34.8', 'O34.9', 'O36.5', 'O36.0', 'O36.1', 'O35.9', 'O36.2', 'O40', 'O41.0', 'O41.1',
             'O41.8', 'O41.9', 'I01.2', 'I34', 'I35', 'I36', 'I37', 'I40', 'I41', 'I41.0', 'I41.1', 'I41.2', 'I41.8',
             'I47.0', 'I49.0', 'I49.4', 'I51.4', 'I51.6', 'O10', 'O16', 'O99.4', 'I23.6', 'I24.0', 'I26', 'I51.3',
             'I63', 'I63.0', 'I63.1', 'I63.2', 'I63.3', 'I63.4', 'I63.5', 'I63.6', 'I63.8', 'I63.9', 'I67.6',
             'I60', 'I60.0', 'I60.1', 'I60.2', 'I60.3', 'I60.4', 'I60.5', 'I60.6', 'I60.7', 'I60.8', 'I60.9',
             'I61', 'I61.0', 'I61.1', 'I61.2', 'I61.3', 'I61.4', 'I61.5', 'I61.6', 'I61.8', 'I61.9', 'I62', 'I62.0',
             'I62.1', 'I62.9', 'I64', 'I64.0', 'I64.1', 'I65', 'I65.0', 'I65.1', 'I65.2', 'I65.3',  'I65.8', 'I65.9',
             'I66', 'I66.0', 'I66.1', 'I66.2', 'I66.3', 'I66.4',  'I66.8', 'I66.9', 'I67', 'I67.0', 'I67.1', 'I67.2',
             'I67.3', 'I67.4', 'I67.5', 'I67.6', 'I67.7', 'I67.8', 'I67.9',
             'I74', 'I80', 'I81', 'I82', 'I87.0', 'G08', 'K75.1', 'O03.2', 'O03.7',  'O04.2',  'O04.7',  'O05.2',
             'O05.7', 'O06.2',  'O06.7', 'O07.2',  'O07.7', 'O08.2',  'O08.7', 'O22.2', 'O22.3', 'O22.5', 'O22.8',
             'O22.9', 'O87.1', 'O87.3', 'O88', 'O99.5', 'D89.9', 'I13.1', 'I13.2', 'N18.8', 'N18.9', 'O10.2', 'O10.3',
             'O99.6', 'E01', 'E01.0', 'E01.1', 'E01.2', 'E01.8', 'Е02', 'E03', 'E03.0', 'E03.1', 'E03.2', 'E03.3', 'E03.4',
             'E03.5', 'E03.6', 'E03.7', 'E03.8', 'E03.9', 'E04', 'E04.0', 'E04.1', 'E04.2', 'E04.3', 'E04.4', 'E04.5',
             'E04.6', 'E04.7', 'E04.8', 'E04.9', 'E05', 'E05.0', 'E05.1', 'E05.2', 'E05.3', 'E05.4', 'E05.5', 'E05.6',
             'E05.7', 'E05.8', 'E05.9', 'E06', 'E06.0', 'E06.1', 'E06.2', 'E06.3', 'E06.4', 'E06.5', 'E06.6', 'E06.7',
             'E06.8', 'E06.9', 'E07', 'E07.0', 'E07.1', 'E07.2', 'E07.3', 'E07.4', 'E07.5', 'E07.6', 'E07.7', 'E07.8',
             'E07.9', 'E27.1',  'E27.2',  'E27.3',  'E27.4', 'O90.5', 'O99.2', 'H52.1', 'H33.0', 'H33.2', 'H33.4',
             'H33.5', 'H40.1', 'H40.2', 'H40.3', 'H40.4', 'H40.5', 'H40.6', 'H40.8', 'H40.9', 'H42', 'H42.0', 'H42.8',
             'D68.0', 'D69.3',  'D69.4', 'D69.5', 'D69.6', 'D66', 'D67', 'D68.1', 'D68.2', 'O99.0', 'O99.1', 'G40',
             'G41', 'G83.3', 'F80.3', 'R56.8', 'O99.3', 'G70', 'G70.0', 'G70.1', 'G70.2', 'G70.8', 'G70.9', 'I28.1',
             'I71', 'I72', 'Q27.3', 'I77.0', 'I67.1', 'I25.4', 'I25.3', 'S02', 'S02.0', 'S02.1', 'S02.2', 'S02.3',
             'S02.4', 'O28.4', 'O26.7', 'O43.0', 'P02.3', 'О36.2', 'O36.0', 'P00.2', 'P56.0', 'P56.9', 'P83.2', 'O35.0',
             'O35.99', 'O35.9', 'P00.6', 'Q62', 'Q64.2', 'Q03', 'D25',  'D26', 'D28.9', 'D28.7', 'O34.1', 'O34.4',
             'D27', 'O99.8', 'D28.0', 'D28.1', 'O28.8', 'S32', 'S32.0', 'S32.1', 'S32.2', 'S32.3', 'S32.4', 'S32.5',
             'S32.7', 'S32.8', 'S33', 'S33.0', 'S33.1', 'S33.2', 'S33.3', 'S33.4', 'S33.5', 'S33.6', 'S33.7', 'S34']
}
risk_rates_blockID = {'low': [],
                      'middle': [],
                      'high': ['(P70-P74)', '(P75-P78)', '(I05-I09)', '(M30-M36)', '(Q60-Q64)', '(E10-E14)',
                               '(D55-D59)', '(D60-D64)', '(C00-C14)',
                               '(C15-C26)', '(C30-C39)', '(C40-C41)', '(C43-C44)', '(C45-C49)', '(C50))', '(C51-C58)',
                               '(C60-C63)', '(C64-C68)', '(C69-C72)', '(C73-C75)', '(C76-C80)', '(C81-C96)', '(C97))',
                               '(K70-K77)', '(D50-D53)', '(S06-S09)']}

HIV_diags = ['B20', 'B21', 'B22', 'B23', 'B24', 'O98.7']
syphilis_diags = ['A50', 'A51', 'A52', 'A53']
hepatitis_diags = ['B15', 'B16', 'B17', 'B18', 'B19', 'K73', 'K70.1', 'K71.2', 'K71.3', 'K71.4', 'K71.5', 'K71.6']
tuberculosis_diags = ['A15', 'A16', 'A17', 'A18', 'A19', 'P37.0']
scabies_diags = ['B86']
pediculosis_diags = ['B85']
multiple_birth = ['O30']
hypertensia = ['O10']
kidney_diseases = ['N00', 'N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N07', 'N08', 'N10', 'N11', 'N12', 'N13', 'N14',
                   'N15', 'N16', 'N17', 'N18', 'N19', 'N20', 'N21', 'N22', 'N23', 'N25', 'N26', 'N27', 'N28', 'N29',
                   'N25-N29', 'O23.0']
collagenoses = ['Q79.6', 'Q87.4', 'Q78.0', 'M33.0', 'M33.1', 'M33.2', 'L94.0', 'M34.0', 'M35.0', 'D69.0', 'D89.1',
                'Q81', 'M05', 'M32', 'L95']
vascular_diseases = ['I70', 'I71', 'I72', 'I73', 'I74', 'I75', 'I76', 'I77', 'I78', 'I79', 'O22']
diabetes = ['E10', 'E11', 'E12', 'E13', 'E14', 'O24']
antiphospholipid_syndrome = ['I82.9', 'D68.8', 'D89.9']

week_postfix = {1: u'я', 2: u'и', 3: u'и', 4: u'и', 5: u'ь',  6: u'ь', 7: u'ь', 8: u'ь', 9: u'ь', 0: u'ь'}


def get_action(event, flat_code, create=False):
    """
    Поиск и создание действия внутри обращения
    :param event: Обращение
    :param flat_code: flat code типа действия
    :param create: создавать ли, если нет?
    :type event: application.models.event.Event
    :type flat_code: list|tuple|basestring|None
    :type create: bool
    :return: действие
    :rtype: Action | None
    """
    query = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0)
    if isinstance(flat_code, (list, tuple)):
        query = query.filter(ActionType.flatCode.in_(flat_code))
    elif isinstance(flat_code, basestring):
        query = query.filter(ActionType.flatCode == flat_code)
    elif flat_code is None:
        return
    else:
        raise TypeError('flat_code must be list|tuple|basestring|None')
    action = query.first()
    if action is None and create:
        action = create_action(get_action_type_id(flat_code), event)
    return action


def get_action_list(event, flat_code, all=False):
    """
    Поиск действий внутри обращения
    :param event: Обращение
    :param flat_code: flat code типа действия
    :type event: application.models.event.Event
    :type flat_code: list|tuple|basestring|None
    :return: действие
    :rtype: sqlalchemy.orm.Query
    """
    query = Action.query.join(ActionType).filter(Action.event == event, Action.deleted == 0)
    if isinstance(flat_code, (list, tuple)):
        query = query.filter(ActionType.flatCode.in_(flat_code))
    elif isinstance(flat_code, basestring):
        query = query.filter(ActionType.flatCode == flat_code)
    elif flat_code is None:
        return
    else:
        raise TypeError('flat_code must be list|tuple|basestring|None')
    if all:
        return query.all()
    return query


def get_action_by_id(action_id, event=None, flat_code=None, create=False):
    """
    :param action_id: id действия
    :param event: обращение, в котором действие может быть создано
    :param flat_code: flat code, с которым действие может быть создано
    :param create: создавать ли действие, если оно не найдено?
    :type action_id: int | None
    :type event: application.models.event.Event
    :type flat_code: str
    :type create: bool
    :return: Действие
    :rtype: Action | None
    """
    action = None
    if action_id:
        query = Action.query.filter(Action.id == action_id, Action.deleted == 0)
        action = query.first()
    elif create:
        action = create_action(get_action_type_id(flat_code), event)
    return action


def action_apt_values(action, codes):
    """
    Получение справочника всех возможных значений свойств действия по кодам
    :param action: Действие
    :param codes: Коды
    :type action: Action
    :type codes: list|tuple
    :rtype: dict
    """
    return dict((key, safe_traverse_attrs(action.propsByCode.get(key), 'value')) for key in codes)


@cache.memoize()
def get_action_type_id(flat_code):
    """
    Получение ActionType.id по его flat code
    :param flat_code: flat code
    :type flat_code: str
    :rtype: int | None
    :return: ActionType.id или None
    """
    selectable = db.select((ActionType.id, ), whereclause=ActionType.flatCode == flat_code, from_obj=ActionType)
    row = db.session.execute(selectable).first()
    if not row:
        return None
    return row[0]


def get_action_property_value(action_id, prop_type_code):
    """
    Получение ActionProperty по ActionPropertyType.code
    :param action_id: Action.id
    :type action_id: int
    :param prop_type_code: ActionPropertyType.code
    :type prop_type_code: str
    :rtype: ActionProperty | None
    :return: ActionProperty или None
    """
    query = ActionProperty.query.join(ActionPropertyType).filter(
        ActionProperty.action_id == action_id,
        ActionProperty.deleted == 0,
        ActionPropertyType.code == prop_type_code
    ).options(
        lazyload('*')
    )
    return query.first()


def get_last_checkup_date(event_id):
    query = db.session.query(Action.begDate).join(ActionType).filter(
        Action.event_id == event_id,
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)
    ).order_by(Action.begDate.desc()).first()
    return query[0] if query else None


def get_event_diag_mkbs(event, **kwargs):
    query = db.session.query(Event).join(
        Diagnostic, Diagnosis
    ).join(
        MKB, Diagnosis.MKB == MKB.DiagID
    ).filter(
        Event.id == event.id,
        Diagnostic.deleted == 0,
        Diagnosis.deleted == 0
    )
    if 'at_flatcodes' in kwargs:
        at_flatcodes = kwargs['at_flatcodes']
        if isinstance(at_flatcodes, (list, tuple)):
            query = query.join(
                (Action, Diagnostic.action_id == Action.id),
                ActionType
            ).filter(
                ActionType.flatCode.in_(at_flatcodes),
                Action.deleted == 0
            )
    if 'action_id' in kwargs:
        action_id = kwargs['action_id']
        query = query.filter(Diagnostic.action_id == action_id)
    if 'without_action_id' in kwargs:
        action_id = kwargs['without_action_id']
        query = query.filter(Diagnostic.action_id != action_id)
    if 'opened' in kwargs:
        if kwargs['opened']:
            query = query.filter(Diagnostic.endDate.is_(None))
        else:
            query = query.filter(Diagnostic.endDate.isnot(None))
    query = query.with_entities(MKB)
    return query.all()


def close_open_checkups(event_id):
    open_checkups = db.session.query(Action).join(ActionType).filter(
        Action.event_id == event_id,
        Action.endDate.is_(None),
        Action.deleted == 0,
        ActionType.flatCode.in_(checkup_flat_codes)
    ).all()
    for action in open_checkups:
        action.endDate = datetime.datetime.now()
        action.status = ActionStatus.finished[0]
        db.session.add(action)
    if open_checkups:
        db.session.commit()


@cache.memoize()
def pregnancy_pathologies():
    query = db.session.query(rbPregnancyPathology)
    result = dict((rb_pp.code, [safe_dict(mkb) for mkb in rb_pp.mkbs]) for rb_pp in query)
    return result


@cache.memoize()
def risk_mkbs():
    query = db.session.query(rbPerinatalRiskRate)
    result = dict((rb_prr.code, [safe_dict(mkb) for mkb in rb_prr.mkbs]) for rb_prr in query)
    return result


def is_event_late_first_visit(event):
    result = False
    fi = get_action(event, first_inspection_code)
    if fi:
        preg_week = fi[inspection_preg_week_code]
        if preg_week is not None:
            result = preg_week >= 10
    return result


def format_action_data(json_data):
    set_person_id = safe_traverse(json_data, 'set_person', 'id')
    person_id = safe_traverse(json_data, 'person', 'id')
    data = {
        'begDate': safe_datetime(json_data['beg_date']),
        'endDate': safe_datetime(json_data['end_date']),
        'plannedEndDate': safe_datetime(json_data['planned_end_date']),
        'directionDate': safe_datetime(json_data['direction_date']),
        'isUrgent': json_data['is_urgent'],
        'status': json_data['status']['id'],
        'setPerson_id': set_person_id,
        'person_id':  person_id,
        'setPerson': Person.query.get(set_person_id) if set_person_id else None,
        'person':  Person.query.get(person_id) if person_id else None,
        'note': json_data['note'],
        'amount': json_data['amount'],
        'account': json_data['account'] or 0,
        'uet': json_data['uet'],
        'payStatus': json_data['pay_status'] or 0,
        'coordDate': safe_datetime(json_data['coord_date']),
        'office': json_data['office'],
        'properties': json_data['properties']
    }
    return data