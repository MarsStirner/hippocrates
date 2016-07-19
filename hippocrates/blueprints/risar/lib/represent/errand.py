# -*- coding: utf-8 -*-
import datetime

from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.common import represent_file_meta
from nemesis.lib.utils import safe_dict
from nemesis.models.enums import ErrandStatus

__author__ = 'viruzzz-kun'


def represent_errand(errand_info):
    today = datetime.date.today()
    planned = errand_info.plannedExecDate.date()
    create_date = errand_info.createDatetime.date()

    days_to_complete = (planned-create_date).days
    progress = (today - create_date).days*100/days_to_complete if (today < planned and days_to_complete) else 100
    card_attrs_action = PregnancyCard.get_for_event(errand_info.event).attrs
    return {
        'id': errand_info.id,
        'create_datetime': errand_info.createDatetime,
        'number': errand_info.number,
        'set_person': errand_info.setPerson,
        'exec_person': errand_info.execPerson,
        'text': errand_info.text,
        'communications': errand_info.communications,
        'planned_exec_date': errand_info.plannedExecDate,
        'exec_date': errand_info.execDate,
        'event': {'id': errand_info.event.id,
                  'external_id':  errand_info.event.externalId,
                  'client': errand_info.event.client.shortNameText,
                  'risk_rate': card_attrs_action['prenatal_risk_572'].value
                  },
        'result': errand_info.result,
        'reading_date': errand_info.readingDate,
        'status': ErrandStatus(errand_info.status_id),
        'progress': progress
    }


def represent_errand_summary(errand):
    return {
        'id': errand.id,
        'number': errand.number,
        'event': {
            'id': errand.event.id,
            'external_id':  errand.event.externalId,
            'client_name': errand.event.client.shortNameText,
        },
        'status': ErrandStatus(errand.status_id),
    }


def represent_errand_shortly(errand):
    return {
        'id': errand.id,
        'create_datetime': errand.createDatetime,
        'number': errand.number,
        'set_person_id': errand.setPerson_id,
        'exec_person_id': errand.execPerson_id,
        'text': errand.text,
        'communications': errand.communications,
        'planned_exec_date': errand.plannedExecDate,
        'exec_date': errand.execDate,
        'event_id': errand.event_id,
        'result': errand.result,
        'reading_date': errand.readingDate,
        'status': ErrandStatus(errand.status_id)
    }


def represent_errand_edit(errand):
    res = represent_errand_shortly(errand)
    res.update({
        'set_person': errand.setPerson,
        'exec_person': errand.execPerson,
        'errand_files': [
            represent_errand_file(ea)
            for ea in errand.attach_files
        ]
    })
    return res


def represent_errand_file(errand_attach):
    res = safe_dict(errand_attach)
    res.update({
        'file_meta': represent_file_meta(errand_attach.file_meta)
    })
    return res