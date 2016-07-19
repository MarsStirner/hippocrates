# -*- coding: utf-8 -*-
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.represent.pregnancy import represent_pregnancy_card_attributes
from nemesis.models.event import Event


def get_debug_data(request_args):
    debug_data = None
    if request_args.get('debug', False):
        event_id = request_args.get('event_id')
        event = Event.query.get(event_id)
        card = PregnancyCard.get_for_event(event)
        card_attrs_action = card.get_card_attrs_action(auto=True)
        debug_data = {
            'ca': represent_pregnancy_card_attributes(card_attrs_action)
        }
    return debug_data