# -*- coding: utf-8 -*-

import datetime
from application.lib.data import create_new_action, update_action, ActionException
from application.models.actions import Action, ActionType
from application.models.event import EventLocalContract, Diagnostic, Diagnosis
from application.lib.utils import safe_date, safe_traverse, safe_datetime, logger
from application.models.exists import rbDocumentType
from application.lib.settings import Settings
from application.systemwide import db


class EventSaveException(Exception):
    def __init__(self, message, data=None):
        super(EventSaveException, self).__init__(message)
        self.data = data


def create_new_local_contract(lc_info):
    err_msg = u'Ошибка сохранения обращения'
    lcon = EventLocalContract()

    date = lc_info.get('date_contract')
    number = lc_info.get('number_contract')
    if Settings.getBool('Event.Payment.1CODVD'):
        lcon.dateContract = datetime.date.today()
        lcon.numberContract = ''
    else:
        if not date:
            raise EventSaveException(err_msg, u'Не указана дата заключения договора.')
        lcon.dateContract = date
        if number is None:
            raise EventSaveException(err_msg, u'Не указан номер договора.')
        lcon.numberContract = number

    lcon.coordAgent = lc_info.get('coord_agent', '')
    lcon.coordInspector = lc_info.get('coord_inspector', '')
    lcon.coordText = lc_info.get('coord_text', '')
    lcon.sumLimit = lc_info.get('sum_limit', 0.0)
    lcon.lastName = lc_info.get('last_name')
    lcon.firstName = lc_info.get('first_name')
    lcon.patrName = lc_info.get('patr_name')
    lcon.birthDate = safe_date(lc_info.get('birth_date'))

    doc_type_id = safe_traverse(lc_info, 'doc_type', 'id')
    lcon.documentType_id = doc_type_id
    lcon.documentType = rbDocumentType.query.get(doc_type_id) if doc_type_id else None
    lcon.serialLeft = lc_info.get('serial_left')
    lcon.serialRight = lc_info.get('serial_right')
    lcon.number = lc_info.get('number')
    lcon.regAddress = lc_info.get('reg_address')
    lcon.org_id = safe_traverse(lc_info, 'payer_org', 'id')
    return lcon


def _check_shared_local_contract_changes(lc_info):
    def _has_changes(lc, lc_info):
        if (lc.numberContract != lc_info.get('number_contract', '')
                or lc.lastName != lc_info.get('last_name', '')
                or lc.firstName != lc_info.get('first_name', '')
                or lc.patrName != lc_info.get('patr_name', '')
                or lc.birthDate != safe_date(lc_info.get('birth_date', ''))
                or lc.documentType_id != safe_traverse(lc_info, 'doc_type', 'id')
                or lc.serialLeft != lc_info.get('serial_left', '')
                or lc.serialRight != lc_info.get('serial_right', '')
                or lc.number != lc_info.get('number', '')
                or lc.regAddress != lc_info.get('reg_address', '')
                or lc.org_id != safe_traverse(lc_info, 'payer_org', 'id')):
            return True
        return False

    lc_id = lc_info.get('id')
    lcon = EventLocalContract.query.get(lc_id)
    return _has_changes(lcon, lc_info)


def get_local_contract_for_new_event(lc_info):
    lc_id = None
    if lc_info:
        lc_id = lc_info.get('id')
    if lc_id:
        if _check_shared_local_contract_changes(lc_info):
            lcon = create_new_local_contract(lc_info)
        else:
            lcon = EventLocalContract.query.get(lc_id)
    else:
        lcon = create_new_local_contract(lc_info)
    return lcon


def create_or_update_local_contract(event, lc_info):
    lc_id = lc_info.get('id')
    # number_contract = lc_info.get('number_contract', '')
    last_name = lc_info.get('last_name', '')
    first_name = lc_info.get('first_name', '')
    patr_name = lc_info.get('patr_name', '')
    birth_date = safe_date(lc_info.get('birth_date', ''))
    document_type_id = safe_traverse(lc_info, 'doc_type', 'id')
    serial_left = lc_info.get('serial_left', '')
    serial_right = lc_info.get('serial_right', '')
    doc_number = lc_info.get('number', '')
    reg_address = lc_info.get('reg_address', '')
    org_id = safe_traverse(lc_info, 'payer_org', 'id')
    if event.id:
        if not event.localContract_id:
            lc = get_local_contract_for_new_event(lc_info)
        else:
            if not lc_id or (
                lc_id and lc_info.get('shared_in_events') and _check_shared_local_contract_changes(lc_info)
            ):
                lc = create_new_local_contract(lc_info)
            else:
                lc = EventLocalContract.query.get(lc_id)
                lc.lastName = last_name
                lc.firstName = first_name
                lc.patrName = patr_name
                lc.birthDate = birth_date
                lc.documentType_id = document_type_id
                lc.serialLeft = serial_left
                lc.serialRight = serial_right
                lc.number = doc_number
                lc.regAddress = reg_address
                lc.org_id = org_id
    else:
        lc = get_local_contract_for_new_event(lc_info)
    return lc


def create_services(event_id, service_groups, contract_id):
    """
    Создание или обновление услуг (действий) и последующее сохранение в бд.
    """
    actions = []
    errors = []
    for sg in service_groups:
        for act_data in sg['actions']:
            action_id = act_data['action_id']
            action_type = ActionType.query.get(sg['at_id'])
            data = {
                'amount': act_data.get('amount', 1),
                'account': act_data.get('account', 0),
                'coordDate': safe_datetime(act_data.get('coord_date')),
                'coordPerson_id': safe_traverse(act_data, 'coord_person', 'id')
            }
            if sg['is_lab']:
                data['plannedEndDate'] = safe_datetime(act_data['planned_end_date'])
            assigned = act_data['assigned'] if sg['is_lab'] else None

            try:
                if not action_id:
                    data['contract_id'] = contract_id
                    action = create_new_action(
                        sg['at_id'],
                        event_id,
                        assigned=assigned,
                        data=data
                    )
                else:
                    if assigned:
                        data['properties_assigned'] = assigned
                    action = Action.query.get(action_id)
                    action = update_action(action, **data)
            except ActionException, e:
                db.session.rollback()
                err_msg = u'Ошибка сохранения услуги "%s": %s.' % (action_type.name, e.message)
                logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                errors.append(err_msg)
            except Exception, e:
                db.session.rollback()
                err_msg = u'Ошибка сохранения услуги "%s"' % action_type.name
                logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                errors.append(err_msg)
            else:
                db.session.add(action)
                try:
                    db.session.commit()
                except Exception, e:
                    db.session.rollback()
                    err_msg = u'Ошибка сохранения услуги "%s"' % action_type.name
                    logger.error(err_msg + u'для event_id=%s' % event_id, exc_info=True)
                    errors.append(err_msg)
                else:
                    actions.append(action)
    return actions, errors


def create_or_update_diagnosis(event, json_data, action=None):
    diagnostic_id = safe_traverse(json_data, 'id')
    set_date = safe_datetime(safe_traverse(json_data, 'set_date'))
    end_date = safe_datetime(safe_traverse(json_data, 'end_date'))
    diagnosis_type_id = safe_traverse(json_data, 'diagnosis_type', 'id')
    character_id = safe_traverse(json_data, 'character', 'id')
    person_id = safe_traverse(json_data, 'person', 'id')
    speciality_id = safe_traverse(json_data, 'person', 'speciality', 'id')
    notes = safe_traverse(json_data, 'notes')
    result_id = safe_traverse(json_data, 'result', 'id')
    ache_result_id = safe_traverse(json_data, 'ache_result', 'id')
    health_group_id = safe_traverse(json_data, 'health_group', 'id')
    trauma_type_id = safe_traverse(json_data, 'trauma_type', 'id')
    phase_id = safe_traverse(json_data, 'phase', 'id')
    diagnosis_description = safe_traverse(json_data, 'diagnosis_description')
    stage_id = safe_traverse(json_data, 'stage', 'id')
    dispanser_id = safe_traverse(json_data, 'dispanser', 'id')
    # sanatorium_id = safe_traverse(json_data, 'sanatorium', 'id'),
    # hospital_id = safe_traverse(json_data, 'hospital', 'id'),

    diagnosis = safe_traverse(json_data, 'diagnosis')
    diagnosis_id = safe_traverse(diagnosis, 'id')
    client_id = event.client_id
    mkb = safe_traverse(diagnosis, 'mkb', 'code')
    mkbex = safe_traverse(diagnosis, 'mkbex', 'code')
    if diagnostic_id:
        diag = Diagnostic.query.get(diagnostic_id)
        diag.setDate = set_date
        diag.endDate = end_date
        diag.diagnosisType_id = diagnosis_type_id
        diag.character_id = character_id
        diag.person_id = person_id
        diag.speciality_id = speciality_id
        diag.notes = notes
        diag.result_id = result_id
        diag.rbAcheResult_id = ache_result_id
        diag.healthGroup_id = health_group_id
        diag.traumaType_id = trauma_type_id
        diag.phase_id = phase_id
        diag.stage_id = stage_id
        diag.dispanser_id = dispanser_id
        diag.diagnosis_description = diagnosis_description

        diagnosis = filter(lambda ds: ds.id == diagnosis_id, diag.diagnoses)
        if not diagnosis:
            raise Exception('Diagnosis record can\'t be found')
        else:
            diagnosis = diagnosis[0]
        diagnosis.MKB = mkb
        diagnosis.MKBEx = mkbex or ''
    else:
        diag = Diagnostic()
        diag.event = event
        diag.setDate = safe_date(set_date)
        diag.endDate = safe_date(end_date)
        diag.diagnosisType_id = diagnosis_type_id
        diag.character_id = character_id
        diag.person_id = person_id
        diag.speciality_id = speciality_id
        diag.notes = notes
        diag.result_id = result_id
        diag.rbAcheResult_id = ache_result_id
        diag.healthGroup_id = health_group_id
        diag.traumaType_id = trauma_type_id
        diag.phase_id = phase_id
        diag.stage_id = stage_id
        diag.dispanser_id = dispanser_id
        diag.diagnosis_description = diagnosis_description
        if action:
            diag.action = action
        # etc
        diag.stage_id = None
        diag.dispanser_id = None
        diag.sanatorium = 0
        diag.hospital = 0

        diagnosis = Diagnosis()
        diagnosis.client_id = client_id
        diagnosis.MKB = mkb
        diagnosis.MKBEx = mkbex or ''
        diagnosis.diagnosisType_id = diagnosis_type_id
        diagnosis.character_id = character_id
        diagnosis.traumaType_id = trauma_type_id
        diagnosis.setDate = safe_date(set_date)
        diagnosis.endDate = safe_date(set_date)
        diagnosis.person_id = person_id
        # etc
        diagnosis.dispanser_id = None
        diagnosis.mod_id = None

        diag.diagnoses.append(diagnosis)

    return diag


def delete_diagnosis(diagnostic):
    """
    :type diagnostic: application.models.event.Diagnostic
    :param diagnostic:
    :return:
    """
    diagnostic.deleted = 1
    for ds in diagnostic.diagnoses:
        ds.deleted = 1
    db.session.add(diagnostic)
