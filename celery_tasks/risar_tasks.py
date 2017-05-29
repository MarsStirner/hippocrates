# coding: utf-8

import datetime

from celery.utils.log import get_task_logger

from hippocrates.blueprints.risar.lib.specific import SystemMode
from nemesis.app import app
from nemesis.models.actions import Action, ActionType

from hippocrates.blueprints.risar.lib import sirius
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.card_attrs import reevaluate_card_fill_rate_all
from hippocrates.blueprints.risar.lib.checkups import \
    validate_send_to_mis_checkup
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_event_cfrs
from hippocrates.blueprints.risar.risar_config import request_type_pregnancy, \
    inspections_span_flatcodes, first_inspection_flat_code, \
    second_inspection_flat_code, pc_inspection_flat_code, \
    puerpera_inspection_flat_code, risar_gyn_checkup_flat_codes, \
    risar_gyn_checkup_flat_code
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.utils import safe_dict, safe_traverse
from nemesis.models.celery_tasks import TaskInfo
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.systemwide import celery, db


logger = get_task_logger(__name__)


@celery.task(bind=True)
def update_card_attrs_cfrs(self):
    new_task = TaskInfo()
    new_task.start_datetime = datetime.datetime.now()
    new_task.task_name = update_card_attrs_cfrs.__name__
    new_task.celery_task_uuid = self.request.id

    task_data = {}

    # before
    event_list = db.session.query(Event).join(
        EventType, rbRequestType
    ).filter(
        Event.deleted == 0,
        Event.execDate.is_(None),
        rbRequestType.code == request_type_pregnancy
    ).order_by(Event.setDate).all()
    cfrs_before = []
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        if not card or not card.attrs:
            logger.critical('event {0} is not valid'.format(event.id))
            continue
        cfrs_before.append({
            'event_id': event.id,
            'card_fill_rates': represent_event_cfrs(card.attrs)
        })
    task_data['cfrs_before'] = cfrs_before
    new_task.task_data = json_dumps(task_data, pretty=True)
    db.session.add(new_task)
    db.session.commit()

    # work
    logger.info('starting card cfrs update')
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        if not card or not card.attrs:
            continue
        reevaluate_card_fill_rate_all(card)
    db.session.commit()
    logger.info('card cfrs update finished')

    # after
    cfrs_after = []
    for event in event_list:
        card = PregnancyCard.get_for_event(event)
        if not card or not card.attrs:
            continue
        cfrs_after.append({
            'event_id': event.id,
            'card_fill_rates': represent_event_cfrs(card.attrs)
        })
    task_data['cfrs_after'] = cfrs_after

    diff = []
    for b, a in zip(cfrs_before, cfrs_after):
        if safe_dict(b) != safe_dict(a):
            logger.debug(u'diff in {0} and {1}'.format(b, a))
            diff.append((b, a))
    task_data['diff'] = diff

    new_task.task_data = json_dumps(task_data, pretty=True)
    new_task.finish_datetime = datetime.datetime.now()
    db.session.add(new_task)
    db.session.commit()
    return safe_dict(diff)


@celery.task(bind=True)
def close_yesterday_checkups(self):
    def get_all_opened_checkups(day):
        return Action.query.join(ActionType).filter(
            Action.deleted == 0,
            Action.begDate < day.date(),
            Action.begDate > (day.date() - datetime.timedelta(days=60)),
            Action.endDate.is_(None),
            ActionType.flatCode.in_(inspections_span_flatcodes + risar_gyn_checkup_flat_codes),
        ).all()

    today = datetime.datetime.today()
    cur_weekday = today.weekday()
    if cur_weekday < 5:  # раньше субботы
        app_mode = safe_traverse(app.config, 'system_prefs', 'mode', default=SystemMode.normal[0])
        if app_mode == SystemMode.tula_mis[0]:
            opened_checkups = get_all_opened_checkups(today - datetime.timedelta(days=1))
        else:
            opened_checkups = get_all_opened_checkups(today)

        for checkup in opened_checkups:
            send_data_to_mis = True
            if checkup.actionType.flatCode == first_inspection_flat_code:
                checkup_method_name = 'risar.api_checkup_obs_first_get'
                checkup_entity_code = sirius.RisarEntityCode.CHECKUP_OBS_FIRST
                ticket_method_name = 'risar.api_checkup_obs_first_ticket25_get'
                ticket_entity_code = sirius.RisarEntityCode.CHECKUP_OBS_FIRST_TICKET
                act_id_name = 'exam_obs_id'
            elif checkup.actionType.flatCode == second_inspection_flat_code:
                checkup_method_name = 'risar.api_checkup_obs_second_get'
                checkup_entity_code = sirius.RisarEntityCode.CHECKUP_OBS_SECOND
                ticket_method_name = 'risar.api_checkup_obs_second_ticket25_get'
                ticket_entity_code = sirius.RisarEntityCode.CHECKUP_OBS_SECOND_TICKET
                act_id_name = 'exam_obs_id'
            elif checkup.actionType.flatCode == pc_inspection_flat_code:
                checkup_method_name = 'risar.api_checkup_pc_get'
                checkup_entity_code = sirius.RisarEntityCode.CHECKUP_PC
                ticket_method_name = 'risar.api_checkup_pc_ticket25_get'
                ticket_entity_code = sirius.RisarEntityCode.CHECKUP_PC_TICKET
                act_id_name = 'exam_pc_id'
            elif checkup.actionType.flatCode == puerpera_inspection_flat_code:
                checkup_method_name = 'risar.api_checkup_puerpera_get'
                # checkup_entity_code = sirius.RisarEntityCode.CHECKUP_
                ticket_method_name = 'risar.api_checkup_puerpera_ticket25_get'
                # ticket_entity_code = sirius.RisarEntityCode.CHECKUP_
                # act_id_name = '
                send_data_to_mis = False
            elif checkup.actionType.flatCode == risar_gyn_checkup_flat_code:
                checkup_method_name = 'risar.api_checkup_gyn_get'
                # checkup_entity_code = sirius.RisarEntityCode.CHECKUP_
                ticket_method_name = 'risar.api_checkup_gyn_ticket25_get'
                # ticket_entity_code = sirius.RisarEntityCode.CHECKUP_
                # act_id_name = '
                send_data_to_mis = False
            else:
                raise Exception(
                    'Unexpected checkup action type = (%s)' %
                    checkup.actionType.flatCode
                )

            if validate_send_to_mis_checkup(checkup):
                checkup.endDate = today
                db.session.add(checkup)
                # чтобы дата закрытия попала в данные при передаче в мис
                db.session.commit()
            else:
                send_data_to_mis = False

            if send_data_to_mis:
                try:
                    sirius.send_to_mis(
                        sirius.RisarEvents.CLOSE_CHECKUP,
                        checkup_entity_code,
                        sirius.OperationCode.READ_ONE,
                        checkup_method_name,
                        obj=(act_id_name, checkup.id),
                        # obj=('external_id', action.id),
                        params={'card_id': checkup.event_id},
                        is_create=False,
                    )
                    sirius.send_to_mis(
                        sirius.RisarEvents.CLOSE_CHECKUP,
                        ticket_entity_code,
                        sirius.OperationCode.READ_ONE,
                        ticket_method_name,
                        obj=(act_id_name, checkup.id),
                        # obj=('external_id', action.id),
                        params={'card_id': checkup.event_id},
                        is_create=False,
                    )
                    sirius.send_to_mis(
                        sirius.RisarEvents.CLOSE_CHECKUP,
                        sirius.RisarEntityCode.MEASURE,
                        sirius.OperationCode.READ_MANY,
                        'risar.api_measure_list_get',
                        obj=('card_id', checkup.event_id),
                        params={'card_id': checkup.event_id},
                        is_create=False,
                    )
                except:
                    # чтобы при устранении проблемы осмотр был найден и передан в мис
                    checkup.endDate = None
                    db.session.add(checkup)
                    db.session.commit()
                    raise


@celery.task(bind=True)
def run_coefficient_calculations(self, year):
    from hippocrates.blueprints.risar.lib.stats import calulate_death_coefficients
    new_task = TaskInfo()
    new_task.start_datetime = datetime.datetime.now()
    new_task.task_name = run_coefficient_calculations.__name__
    new_task.celery_task_uuid = self.request.id
    calulate_death_coefficients(year)
    new_task.finish_datetime = datetime.datetime.now()
    db.session.add(new_task)
    db.session.commit()
    return 'ok'
