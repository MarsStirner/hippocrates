# -*- coding: utf-8 -*-

from nemesis.models.event import Event
from hippocrates.blueprints.risar.lib.represent import represent_pregnancy_card_attributes


def get_debug_data(request_args):
    debug_data = None
    if request_args.get('debug', False):
        event_id = request_args.get('event_id')
        event = Event.query.get(event_id)
        debug_data = {
            'ca': represent_pregnancy_card_attributes(event)
        }
    return debug_data