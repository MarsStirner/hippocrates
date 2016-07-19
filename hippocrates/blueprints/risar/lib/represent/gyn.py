# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.lib.represent.common import represent_event

from hippocrates.blueprints.risar.lib.card import GynecologicCard
from hippocrates.blueprints.risar.lib.card_attrs import check_disease
from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_card_attributes, \
    represent_pregnancy_anamnesis, represent_pregnancy_epicrisis, represent_pregnancy_checkup_shortly

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
        'card_attributes': represent_pregnancy_card_attributes(card_attrs_action),
        'anamnesis': represent_pregnancy_anamnesis(card),
        'epicrisis': represent_pregnancy_epicrisis(event),
        'checkups': map(represent_pregnancy_checkup_shortly, card.checkups),
        'has_diseases': check_disease(all_diagnostics)
    })
    return represent
