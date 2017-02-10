# -*- encoding: utf-8 -*-

from flask import request

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.epicrisis_children import create_or_update_newborns
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_epicrisis, \
    represent_chart_for_epicrisis
from hippocrates.blueprints.risar.lib.notification import NotificationQueue
from hippocrates.blueprints.risar.lib.utils import get_action, close_open_checkups
from hippocrates.blueprints.risar.risar_config import risar_epicrisis
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.diagnosis import create_or_update_diagnoses
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.systemwide import db


@module.route('/api/0/pregnancy/chart/<int:event_id>/epicrisis', methods=['GET', 'POST'])
@api_method
def api_0_chart_epicrisis(event_id):
    event = Event.query.get(event_id)
    card = PregnancyCard.get_for_event(event)

    if not event:
        raise ApiException(404, u'Event не найден')
    if request.method == 'GET':
        action = get_action(event, risar_epicrisis, True)
    else:
        data = request.get_json()
        action_id = data.pop('id', None)
        newborn_inspections = filter(None, data.pop('newborn_inspections', []))
        diagnoses = data.pop('diagnoses', [])
        action = get_action(event, risar_epicrisis, True)

        if not action.id:
            close_open_checkups(event_id)  # закрыть все незакрытые осмотры
            EventMeasureController().close_all_unfinished_ems(action)
        for code, value in data.iteritems():
            if action.has_property(code):
                action.set_prop_value(code, value)
        create_or_update_diagnoses(action, diagnoses)
        create_or_update_newborns(action, newborn_inspections)

        db.session.commit()
        card.reevaluate_card_attrs()
        db.session.commit()
        NotificationQueue.process_events()
    return {
        'chart': represent_chart_for_epicrisis(event),
        'epicrisis': represent_pregnancy_epicrisis(event, action) if action else None
    }


@module.route('/api/0/epicrisis/newborn_inspection/')
@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>', methods=['DELETE'])
@api_method
def api_0_newborn_inspection_delete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        raise ApiException(404, u'Осмотр не найден')
    if inspection.deleted:
        raise ApiException(400, u'Осмотр уже был удален')
    inspection.deleted = 1
    db.session.commit()
    return True


@module.route('/api/0/epicrisis/newborn_inspection/<int:inspection_id>/undelete', methods=['POST'])
@api_method
def api_0_newborn_inspection_undelete(inspection_id):
    inspection = Action.query.get(inspection_id)
    if inspection is None:
        raise ApiException(404, u'Переливание не найдено')
    if not inspection.deleted:
        raise ApiException(400, u'Переливание не является удалённым')
    inspection.deleted = 0
    db.session.commit()
    return True