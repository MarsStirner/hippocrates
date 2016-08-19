#! coding:utf-8
"""


@author: BARS Group
@date: 22.04.2016

"""
from blueprints.risar.lib.card import PregnancyCard
from blueprints.risar.risar_config import general_hospitalizations, \
    general_specialists_checkups
from blueprints.risar.risar_config import checkup_flat_codes
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.models.exists import MKB
from nemesis.models.person import Person
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


def update_patient_diagnoses(old_diag_id, new_em_result):
    """
    корректировка диагнозов пациента, при их изменении в результатах мероприятия
    :param old_diag_id:
    :param new_em_result:
    :param em:
    :return:
    """
    new_em_diag = get_event_measure_diag(new_em_result)
    if not new_em_diag:
        new_diag_id = get_event_measure_diag(new_em_result, raw=True)
        if new_diag_id:
            new_em_diag = MKB.query.get(new_diag_id)
    new_diag_id = new_em_diag and new_em_diag.id
    if new_diag_id != old_diag_id:
        event = new_em_result.event
        pcard = PregnancyCard.get_for_event(event)
        diagnostics = pcard.get_client_diagnostics(event.setDate, event.execDate)
        opened_diags = dict((d.mkb.id, d) for d in diagnostics if not d.diagnosis.endDate)
        if old_diag_id and old_diag_id in opened_diags:
            if not diagnosis_using_by_next_checkups(new_em_result):
                # закрыть
                diagnosis = opened_diags[old_diag_id].diagnosis
                diagnosis.endDate = new_em_result.begDate
        if new_diag_id and new_diag_id not in opened_diags:
            # создать
            person = get_event_measure_doctor(new_em_result)
            if not person:
                person_id = safe_current_user_id()
                person = Person.query.get(person_id)
            diag_data = {
                'diagnostic': {
                    'mkb': new_em_diag.__json__(),
                },
                'person': person and person.__json__(),
                'set_date': new_em_result.begDate,
            }
            create_or_update_diagnoses(new_em_result, [diag_data])


def get_event_measure_diag(em_result, raw=False):
    def get_measure_diag_prop_code(em_result):
        if em_result.actionType.context == general_specialists_checkups:
            return 'MainDiagnosis'
        if em_result.actionType.context == general_hospitalizations:
            return 'FinalDiagnosis'

    prop_type_code = get_measure_diag_prop_code(em_result)
    if raw:
        return prop_type_code and em_result.propsByCode[prop_type_code].value_raw
    else:
        return prop_type_code and em_result.propsByCode[prop_type_code].value


def get_event_measure_doctor(em_result):
    def get_measure_diag_prop_code(em_result):
        if em_result.actionType.context == general_specialists_checkups:
            return 'Doctor'
        if em_result.actionType.context == general_hospitalizations:
            return 'Doctor'

    prop_type_code = get_measure_diag_prop_code(em_result)
    return prop_type_code and em_result.propsByCode[prop_type_code].value


def diagnosis_using_by_next_checkups(action):
    return None


def get_measure_result_mkbs(action, codes):
    res = []
    for code in codes:
        if code in action.propsByCode and action.propsByCode[code].value:
            res.append(action.propsByCode[code].value.DiagID)
    return res
