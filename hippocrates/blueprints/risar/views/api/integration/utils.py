# -*- coding: utf-8 -*-

from nemesis.models.organisation import Organisation
from nemesis.models.person import Person
from nemesis.models.client import Client
from nemesis.models.event import Event
from nemesis.models.actions import Action


def get_org_by_org_code(org_code):
    org = Organisation.query.filter(
        Organisation.regionalCode == org_code,
        Organisation.deleted == 0
    ).first()
    return org


def get_person_by_codes(person_code, org_code):
    person = Person.query.join(Organisation).filter(
        Person.regionalCode == person_code,
        Person.deleted == 0,
        Organisation.regionalCode == org_code,
        Organisation.deleted == 0
    ).first()
    return person


def get_client_query(client_id):
    return Client.query.filter(Client.id == client_id, Client.deleted == 0)


def get_event_query(event_id):
    return Event.query.filter(Event.id == event_id, Event.deleted == 0)


def get_action_query(action_id):
    return Action.query.filter(Action.id == action_id, Action.deleted == 0)