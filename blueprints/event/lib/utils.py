# -*- coding: utf-8 -*-

import datetime
from application.lib.data import create_new_action, update_action
from application.models.actions import Action, ActionType
from application.models.event import EventLocalContract
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


def get_local_contract(lc_info):
    lc_id = None
    if lc_info:
        lc_id = lc_info.get('id')
    if lc_id:
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

        lcon = EventLocalContract.query.get(lc_id)
        if _has_changes(lcon, lc_info):
            lcon = create_new_local_contract(lc_info)
    else:
        lcon = create_new_local_contract(lc_info)
    return lcon


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