# -*- coding: utf-8 -*-
from nemesis.lib.data import create_action
from nemesis.lib.utils import safe_traverse_attrs
from nemesis.models.actions import Action, ActionType
from nemesis.systemwide import cache, db

risk_rates_diagID = {
    'low': ['Z34.0', 'Z34.8', 'Z34.9'],
    'middle': ['I34.1', 'О99.5', 'Е04.0', 'Е04.1', 'Е04.2', 'Е04.3', 'Е04.4', 'Е04.5', 'Е04.6', 'Е04.7', 'Е04.8',
               'Е04.9', 'Н52.1', 'N11.0', 'N11.1', 'N11.2', 'N11.3', 'N11.4', 'N11.5', 'N11.6', 'N11.7', 'N11.8',
               'N11.9', 'N30.1', 'N30.2', 'K29.3', 'K29.4', 'K29.5', 'K29.9', 'K51.1', 'K51.2', 'O48', 'O36.6', 'O33.0',
               'O33.1', 'O33.2', 'O33.3', 'O32.1', 'O44.0', 'Z35.2', 'O30.0', 'O30.1', 'O30.2', 'O30.8', 'O30.9',
               'О34.2', 'O34.2', 'Z35.0', 'O40', 'О42', 'O47.0', 'О36.5'],
    'high': ['O47.0', 'O44', 'O44.0', 'O32.3', 'O14', 'O11', 'O14.1', 'O14.9', 'O15.0', 'O26.6', 'O34.2', 'O08.6',
             'O34.6', 'O36.5', 'O36.0', 'O36.1', 'O35', 'O35.0', 'O35.1', 'O35.2', 'O35.3', 'O35.4', 'O35.5', 'O35.6',
             'O35.7', 'O35.8', 'O35.9', 'O36.2', 'O41.0', 'O41.1', 'O41.8', 'O41.9', 'I51.6', 'I34', 'I47.0',
             'I49.0', 'I49.4', 'I41', 'I41.0', 'I41.1', 'I41.2', 'I41.8', 'I51.4', 'I40', 'I01.2', 'I53.3', 'I67.6',
             'I74', 'O87.3', 'I26', 'O22.5', 'I24.0', 'I80', 'I81', 'I82', 'I63.3', 'O08.7', 'I23.6', 'I24.0', 'O87',
             'G08', 'G95.1', 'K75.1', 'I87.0', 'O88', 'O22.2', 'O22.3', 'O22.9', 'О99.5', 'D89.9', 'I13', 'K71',
             'K71.0', 'K71.1', 'K71.2', 'K71.3', 'K71.4', 'K71.5', 'K71.6', 'K71.7', 'K71.8', 'K71.9', 'K72', 'K72.0',
             'K72.1', 'K72.9', 'K73', 'K73.0', 'K73.1', 'K73.2', 'K73.8', 'K73.9', 'K74', 'K74.0', 'K74.1', 'K74.2',
             'K74.3', 'K74.4', 'K74.5', 'K74.6', 'K75', 'K75.0', 'K75.1', 'K75.2', 'K75.3', 'K75.8', 'K75.9', 'K76',
             'K76.0', 'K76.1', 'K76.2', 'K76.3', 'K76.4', 'K76.5', 'K76.6', 'K76.7', 'K76.8', 'K76.9', 'K77', 'K77.0',
             'K77.8', 'E01', 'E01.0', 'E01.1', 'E01.2', 'E01.8', 'Е02', 'E03.0', 'E03.1', 'E03.2', 'E03.3', 'E03.4',
             'E03.5', 'E03.6', 'E03.7', 'E03.8', 'E03.9', 'E04', 'E04.0', 'E04.1', 'E04.2', 'E04.3', 'E04.4', 'E04.5',
             'E04.6', 'E04.7', 'E04.8', 'E04.9', 'E05', 'E05.0', 'E05.1', 'E05.2', 'E05.3', 'E05.4', 'E05.5',
             'E05.6', 'E05.7', 'E05.8', 'E05.9', 'E06', 'E06.0', 'E06.1', 'E06.2', 'E06.3', 'E06.4', 'E06.5',
             'E06.6', 'E06.7', 'E06.8', 'E06.9', 'E07', 'E07.0', 'E07.1', 'E07.2', 'E07.3', 'E07.4', 'E07.5',
             'E07.6', 'E07.7', 'E07.8', 'E07.9', 'D50', 'D69.6', 'P61.0', 'D68.0', 'O99.1', 'G40', 'G41', 'G83.3',
             'F80.3', 'R56.8', 'G70', 'G70.0', 'G70.1', 'G70.2', 'G70.8', 'G70.9', 'I71', 'I72', 'Q27.3', 'I77.0',
             'I67.1', 'I25.4', 'I25.3', 'O28.3', 'О43.0', 'O31.2', 'O31.8', 'P02.3', 'О36.2', 'O36.0', 'P00.2', 'P60',
             'P61.8', 'P56.0', 'P56.9', 'P83.2', 'O35.9', 'Q33.0', 'Q36.2', 'Q62', 'Q64.2', 'Q03', 'D25', 'O34.1',
             'O34.4', 'D26', 'D28.2', 'D28.9', 'D28.7', 'D27', 'D28.0', 'D28.1', 'O34.6', 'O34.7']
}
risk_rates_blockID = {'low': [],
                      'middle': [],
                      'high': ['(P70-P74)', '(P75-P78)', '(I05-I09)', '(M30-M36)', '(Q60-Q64)', '(E10-E14)',
                               '(H00-H06)', '(H10-H13)', '(H15-H22)', '(H25-H28)', '(H30-H36)', '(H40-H42)',
                               '(H43-H45)', '(H46-H48)', '(H49-H52)', '(H53-H54)', '(H55-H59)', '(H60-H62)',
                               '(H65-H75)', '(H80-H83)', '(H90-H95)', '(D55-D59)', '(D60-D64)', '(C00-C14)',
                               '(C15-C26)', '(C30-C39)', '(C40-C41)', '(C43-C44)', '(C45-C49)', '(C50))', '(C51-C58)',
                               '(C60-C63)', '(C64-C68)', '(C69-C72)', '(C73-C75)', '(C76-C80)', '(C81-C96)', '(C97))']}

HIV_diags = ['B20', 'B21', 'B22', 'B23', 'B24']
syphilis_diags = ['A50', 'A51', 'A52', 'A53']
hepatitis_diags = ['B15', 'B16', 'B17', 'B18', 'B19', 'K73', 'K70.1', 'K71.2', 'K71.3', 'K71.4', 'K71.5', 'K71.6']
tuberculosis_diags = ['A15', 'A16', 'A17', 'A18', 'A19', 'P37.0']
scabies_diags = ['B86']
pediculosis_diags = ['B85']

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


def get_action_by_id(action_id, event, flat_code, create=False):
    """
    :param action_id: id действия
    :param event: обращение, в котором действие может быть создано
    :param flat_code: flat code, с которым действие может быть создано
    :param create: создавать ли действие, если оно не найдено?
    :type action_id: int
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