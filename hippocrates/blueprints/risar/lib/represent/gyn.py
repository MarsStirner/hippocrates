# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.lib.card import GynecologicCard
from hippocrates.blueprints.risar.lib.card_attrs import check_disease
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.represent.common import represent_event, represent_checkup, \
    represent_checkup_shortly, represent_measures, represent_pregnancy, represent_transfusion, represent_intolerance
from hippocrates.blueprints.risar.lib.utils import action_as_dict
from hippocrates.blueprints.risar.risar_config import gyn_checkup_simple_codes
from nemesis.lib.utils import safe_traverse_attrs
from nemesis.models.client import BloodHistory

__author__ = 'viruzzz-kun'


def represent_gyn_event(event):
    """
    :type event: application.models.event.Event
    """
    card = GynecologicCard.get_for_event(event)
    all_diagnostics = card.get_client_diagnostics(event.setDate, event.execDate)
    card_attrs_action = card.get_card_attrs_action(auto=True)
    em_ctrl = EventMeasureController()
    represent = represent_event(event)
    represent.update({
        'em_progress': em_ctrl.calc_event_measure_stats(event),
        'card_attributes': represent_gyn_card_attributes(card_attrs_action),
        'anamnesis': represent_gyn_anamnesis(card),
        'epicrisis': represent_gyn_epicrisis(event),
        'checkups': map(represent_gyn_checkup_shortly, card.checkups),
        'has_diseases': check_disease(all_diagnostics)
    })
    return represent


def represent_gyn_checkup_wm(action):
    result = represent_gyn_checkup(action)
    result['measures'] = represent_measures(action)
    return result


def represent_ticket_25(action):
    if not action:
        return {}
    return action_as_dict(action)


def represent_gyn_checkup(action):
    result = represent_checkup(action, gyn_checkup_simple_codes)
    result['ticket_25'] = represent_ticket_25(action.propsByCode['ticket_25'].value)
    return result


def represent_gyn_card_attributes(action):
    return action_as_dict(action)


def represent_gyn_epicrisis(event):
    return {}


def represent_gyn_checkup_shortly(action):
    return represent_checkup_shortly(action)


def represent_gyn_anamnesis(card):
    return {
        'client_id': card.event.client_id,
        'general': represent_general_anamnesis_action(card.anamnesis),
        'pregnancies': map(represent_pregnancy, card.prev_pregs),
        'transfusions': map(represent_transfusion, card.transfusions),
        'intolerances': map(represent_intolerance, card.intolerances),
    }


def represent_general_anamnesis_action(action):
    if action is None:
        return
    return dict(
        action_as_dict(action),

        blood_type=safe_traverse_attrs(
            BloodHistory.query.filter(
                BloodHistory.client_id == action.event.client_id
            ).order_by(
                BloodHistory.bloodDate.desc()
            ).first(), 'bloodType', default=None)
    )
