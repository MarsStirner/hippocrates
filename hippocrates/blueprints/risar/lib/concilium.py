# coding: utf-8

import itertools

from blueprints.risar.models.risar import RisarConcilium, RisarConcilium_Members


def get_concilium_by_id(concilium_id, event=None, create=False):
    concilium = None
    if concilium_id:
        query = RisarConcilium.query.filter(
            RisarConcilium.id == concilium_id,
        )
        concilium = query.first()
    elif create:
        concilium = create_concilium(event)
    return concilium


def get_concilium_list(event_id):
    return RisarConcilium.query.filter(RisarConcilium.event_id == event_id).all()


def create_concilium(event):
    concilium = RisarConcilium()
    concilium.event_id = event.id
    concilium.event = event
    return concilium


def update_concilium(concilum, data):
    changed = []
    deleted = []
    concilum.date = data['date']
    concilum.hospital_id = data['hospital_id']
    concilum.hospital = data['hospital']
    concilum.doctor_id = data['doctor_id']
    concilum.doctor = data['doctor']
    concilum.patient_presence = data['patient_presence']
    concilum.mkb_id = data['mkb_id']
    concilum.mkb = data['mkb']
    concilum.reason = data['reason']
    concilum.patient_condition = data['patient_condition']
    concilum.decision = data['decision']
    changed.append(concilum)

    chg, dtd = create_or_update_concilium_members(concilum, data['members'])
    changed.extend(chg)
    deleted.extend(dtd)
    return changed, deleted


def create_or_update_concilium_members(concilium, members_data):
    existing_members = concilium.members
    changed = []
    deleted = []
    for new_data, exist_member in itertools.izip_longest(members_data, existing_members):
        if not new_data:
            deleted.append(exist_member)
            continue
        if not exist_member:
            exist_member = RisarConcilium_Members()
            exist_member.concilium_id = concilium.id
            exist_member.concilium = concilium

        exist_member.person_id = new_data['person_id']
        exist_member.person = new_data['person']
        exist_member.opinion = new_data.get('opinion')
        changed.append(exist_member)
    return changed, deleted