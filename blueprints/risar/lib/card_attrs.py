# -*- coding: utf-8 -*-
import itertools
import datetime
from application.lib.data import create_action
from application.lib.jsonify import EventVisualizer
from application.models.actions import Action, ActionType
from application.systemwide import db
from blueprints.risar.lib.utils import get_action, get_action_list, HIV_diags, syphilis_diags, hepatitis_diags, \
    tuberculosis_diags, scabies_diags, pediculosis_diags
from blueprints.risar.risar_config import checkup_flat_codes, risar_mother_anamnesis
from .utils import risk_rates_blockID, risk_rates_diagID

__author__ = 'viruzzz-kun'


def get_card_attrs_action(event, auto=True):
    """
    Получение Action, соответствующего атрибутам карточки
    :param event: карточка беременной, обращение
    :param auto: создавать ли действие автоматически
    :type event: application.models.event.Event
    :type auto: bool
    :return: действие с атрибутами
    :rtype: Action|NoneType
    """
    action = Action.query.join(ActionType).filter(
        Action.event == event,
        ActionType.flatCode == 'cardAttributes',
    ).first()
    if action is None and auto:
        action = create_action(default_AT_Heuristic().id, event)
        reevaluate_card_attrs(event, action)
        db.session.add(action)
        db.session.commit()
    return action


def default_AT_Heuristic():
    """
    Получение ActionType, соответствующего атрибутам карточки
    :rtype: ActionType | None
    """
    return ActionType.query.filter(ActionType.flatCode == 'cardAttributes').first()


def get_all_diagnoses(event):
    """
    Получание всех диагнозов по событию
    :param event: Событие
    :type event: application.models.event.Event
    :return: list of DiagIDs
    """
    result = []
    evis = EventVisualizer()
    for action in event.actions:
        for prop in action.properties:
            if prop.type.typeName == 'Diagnosis' and prop.value:
                if prop.type.isVector:
                    for diagnostic in prop.value:
                        diag = evis.make_diagnostic_record(diagnostic)
                        diag['action_property_name'] = prop.type.name
                        result.append(diag)
                else:
                    diag = evis.make_diagnostic_record(prop.value)
                    diag['action_property_name'] = prop.type.name
                    result.append(diag)
    result.sort(key=lambda x: x['set_date'])
    return result


def calc_risk_rate(event):
    """
    Расчёт риска невынашивания
    :param event: обращение
    :type event: application.models.event.Event
    :rtype: int
    """
    def diag_to_risk_rate(diag):
        if diag['diagnosis']['mkb'].DiagID in risk_rates_diagID['high'] or diag['diagnosis']['mkb'].BlockID in risk_rates_blockID['high']:
            return 3
        elif diag['diagnosis']['mkb'].DiagID in risk_rates_diagID['middle'] or diag['diagnosis']['mkb'].BlockID in risk_rates_blockID['middle']:
            return 2
        elif diag['diagnosis']['mkb'].DiagID in risk_rates_diagID['low'] or diag['diagnosis']['mkb'].BlockID in risk_rates_blockID['low']:
            return 1
        return 0

    all_diagnoses = list(get_all_diagnoses(event))
    return max(map(diag_to_risk_rate, all_diagnoses)) if all_diagnoses else 0


def get_pregnancy_start_date(event):
    """
    Вычислить дату начала беременности
    :param event: обращение
    :type event: application.models.event.Event
    :rtype: datetime.date | None
    :return:
    """
    for inspection in get_action_list(event, checkup_flat_codes).order_by(Action.begDate.desc()):
        if inspection.propsByCode['pregnancy_week'].value:
            return (inspection.begDate - datetime.timedelta(weeks=int(inspection.propsByCode['pregnancy_week'].value))).date()

    mother_action = get_action(event, risar_mother_anamnesis)
    if mother_action:
        return mother_action.propsByCode['menstruation_last_date'].value


def get_predicted_d_date(start_date):
    """
    Вычисление предполагаемой даты родов
    :param start_date: дата начала беременности
    :type start_date: datetime.date
    :rtype: datetime.date
    :return:
    """
    if start_date:
        return start_date + datetime.timedelta(weeks=40)


def reevaluate_card_attrs(event, action=None):
    """
    Пересчёт атрибутов карточки беременной
    :param event: карточка беременной, обращение
    :type event: application.models.event.Event
    """
    preg_start_date = get_pregnancy_start_date(event)
    if action is None:
        action = get_card_attrs_action(event)
    action['prenatal_risk_572'].value = calc_risk_rate(event)
    action['pregnancy_start_date'].value = preg_start_date
    action['predicted_delivery_date'].value = get_predicted_d_date(preg_start_date)


def check_disease(diagnoses):
    has_disease = {'has_HIV': False,
                   'has_syphilis': False,
                   'has_hepatitis': False,
                   'has_tuberculosis': False,
                   'has_scabies': False,
                   'has_pediculosis': False}
    for diag in diagnoses:
        diag_id = diag['diagnosis']['mkb'].DiagID
        if filter(lambda x: x in diag_id, HIV_diags):
            has_disease['has_HIV'] = True
        if filter(lambda x: x in diag_id, syphilis_diags):
            has_disease['has_syphilis'] = True
        if filter(lambda x: x in diag_id, hepatitis_diags):
            has_disease['has_hepatitis'] = True
        if filter(lambda x: x in diag_id, tuberculosis_diags):
            has_disease['has_tuberculosis'] = True
        if filter(lambda x: x in diag_id, scabies_diags):
            has_disease['has_scabies'] = True
        if filter(lambda x: x in diag_id, pediculosis_diags):
            has_disease['has_pediculosis'] = True
    return has_disease