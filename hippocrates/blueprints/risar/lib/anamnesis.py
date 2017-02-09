# -*- coding: utf-8 -*-

from hippocrates.blueprints.risar.risar_config import risar_anamnesis_pregnancy
from hippocrates.blueprints.risar.lib.utils import fill_action_from_another_action, get_action_by_id
from hippocrates.blueprints.risar.models.risar import RisarEpicrisis_Children, RisarPreviousPregnancy_Children
from nemesis.systemwide import db
from nemesis.lib.utils import safe_traverse, safe_traverse_attrs


def copy_anamnesis_from_gyn_card(gyn_card, preg_card):
    preg_card.anamnesis.mother.set_prop_value('menstruation_start_age', gyn_card.anamnesis.get_prop_value('age'))
    preg_card.anamnesis.mother.set_prop_value('menstruation_duration', gyn_card.anamnesis.get_prop_value('duration'))
    preg_card.anamnesis.mother.set_prop_value('menstruation_period', gyn_card.anamnesis.get_prop_value('period_duration'))
    preg_card.anamnesis.mother.set_prop_value('menstruation_disorders', gyn_card.anamnesis.get_prop_value('disorder'))
    preg_card.anamnesis.mother.set_prop_value('sex_life_start_age', gyn_card.anamnesis.get_prop_value('sex_life_age'))
    preg_card.anamnesis.mother.set_prop_value('marital_status', gyn_card.anamnesis.get_prop_value('marital_status'))
    preg_card.anamnesis.mother.set_prop_value('infertility', gyn_card.anamnesis.get_prop_value('infertility'))
    preg_card.anamnesis.mother.set_prop_value('infertility_type', gyn_card.anamnesis.get_prop_value('infertility_kind'))
    preg_card.anamnesis.mother.set_prop_value('infertility_period', gyn_card.anamnesis.get_prop_value('infertility_duration'))
    preg_card.anamnesis.mother.set_prop_value('infertility_cause', gyn_card.anamnesis.get_prop_value('infertility_etiology'))
    preg_card.anamnesis.mother.set_prop_value('infertility_treatment', gyn_card.anamnesis.get_prop_value('infertility_treatment'))
    preg_card.anamnesis.mother.set_prop_value('alcohol', gyn_card.anamnesis.get_prop_value('alcohol'))
    preg_card.anamnesis.mother.set_prop_value('smoking', gyn_card.anamnesis.get_prop_value('smoking'))
    preg_card.anamnesis.mother.set_prop_value('toxic', gyn_card.anamnesis.get_prop_value('toxic'))
    preg_card.anamnesis.mother.set_prop_value('drugs', gyn_card.anamnesis.get_prop_value('drugs'))
    preg_card.anamnesis.mother.set_prop_value('work_group', gyn_card.anamnesis.get_prop_value('work_group'))
    preg_card.anamnesis.mother.set_prop_value('professional_properties', gyn_card.anamnesis.get_prop_value('professional_properties'))


def calculate_preg_result(epicrisis):
    pregnancy_final = safe_traverse(epicrisis.get_prop_value('pregnancy_final'), 'code')
    pregnancy_duration = epicrisis['pregnancy_duration'].value
    code = None
    if pregnancy_final == 'rodami':
        if pregnancy_duration > 42:
            code = 'postmature_birth'
        elif 38 <= pregnancy_duration <= 42:
            code = 'delivery'
        elif 28 <= pregnancy_duration <= 37:
            code = 'premature_birth_28-37'
        elif 22 <= pregnancy_duration <= 27:
            code = 'premature_birth_22-27'
    elif pregnancy_final == 'abortom':
        abort_kind = epicrisis.get_prop_value('abort')
        if abort_kind:
            abort_kind = abort_kind.get('code')
            if abort_kind:
                if abort_kind == "samoproizvol_nyj":
                    if pregnancy_duration <= 11:
                        code = "misbirth_before_11"
                    elif 12 <= pregnancy_duration <= 21:
                        code = "misbirth_before_12-21"
                elif abort_kind in ["'abortmedikamentoznymmetodom-posostoaniurebenka",
                                    'abortmedikamentoznymmetodom-posostoaniujensiny',
                                    'iskusstvennyj-pomed.pokazaniamjensiny',
                                    'iskusstvennyj-pomed.pokazaniamploda',
                                    ]:
                    code = "therapeutic_abortion"
                elif abort_kind == "drugievidypreryvaniaberemennosti(kriminal_nye)":
                    code = "criminal"
                elif abort_kind == "neutocnennye":
                    code = "unknown_miscarriage"
                elif abort_kind == "iskusstvennyj-posozial_nympokazaniam":
                    code = "social_reasons"
                elif abort_kind == "iskusstvennyj-pojelaniujensiny":
                    code = "abortion_by_woman_request"

    if code:
        return {"code": code}


def create_prev_pregn_based_on_epicrisis(from_card, to_card):
    if hasattr(from_card, 'epicrisis'):
        if from_card.epicrisis.exists:
            epic_props = from_card.epicrisis.action
            blank_action = get_action_by_id(None, to_card.event, risar_anamnesis_pregnancy, True)
            deliv_date = epic_props.get_prop_value('delivery_date')
            blank_action.set_prop_value('year', deliv_date.year if deliv_date else None)
            blank_action.set_prop_value('pregnancyResult', calculate_preg_result(epic_props))
            blank_action.set_prop_value('pregnancy_week', epic_props.get_prop_value('pregnancy_duration'))
            caes_section = epic_props.get_prop_value('caesarean_section')
            blank_action.set_prop_value('maternity_aid', [{'code': '05'}] if caes_section else [])
            blank_action.set_prop_value('operation_testimonials', epic_props.get_prop_value('indication'))
            if not blank_action.get_prop_value('card_number'):
                blank_action.set_prop_value('card_number', from_card.event.id)
            db.session.add(blank_action)
            for nb in RisarEpicrisis_Children.query.filter(
                RisarEpicrisis_Children.action_id == epic_props.id
            ).all():
                child = RisarPreviousPregnancy_Children()
                child.action_id = blank_action.id
                child.weight = nb.weight
                child.alive = nb.alive
                child.sex = nb.sex
                db.session.add(child)


def copy_one_preg(action, to_card):
    empty_action = get_action_by_id(None, to_card.event, risar_anamnesis_pregnancy, True)
    fill_action_from_another_action(action, empty_action)
    if not empty_action.get_prop_value('card_number'):
        # теперь мы не хотим ссылку на карту для введенных вручную и мы уже завязались на это поле в интерфейсе
        empty_action.set_prop_value('card_number', -1)
    db.session.add(empty_action)
    db.session.add(empty_action)
    for nb in RisarPreviousPregnancy_Children.query.filter(
        RisarPreviousPregnancy_Children.action_id == action.id
    ).all():
        child = RisarPreviousPregnancy_Children()
        child.action_id = empty_action.id
        child.weight = nb.weight
        child.alive = nb.alive
        child.sex = nb.sex
        db.session.add(child)


def copy_all_prev_pregs(from_card, to_card, own_only=False):
    """копирует предыдущие беременности
    :own_only = True - только введенные руками в этой карте(унаследованные игнорирует)"""
    prev_pregs = [x for x in from_card.prev_pregs if not x.action.get_prop_value('card_number')]\
                                        if own_only is True else from_card.prev_pregs
    for prev in prev_pregs:
        copy_one_preg(prev.action, to_card)


def send_prev_pregnancies_to_gyn_card(pregnancy_event):
    from blueprints.risar.lib.card import PregnancyCard, GynecologicCard
    preg_card = PregnancyCard.get_for_event(pregnancy_event)
    gyn_event = preg_card.latest_gyn_event
    if gyn_event:
        gyn_card = GynecologicCard.get_for_event(gyn_event)
        if gyn_card:
            create_prev_pregn_based_on_epicrisis(from_card=preg_card, to_card=gyn_card)
            copy_all_prev_pregs(from_card=preg_card, to_card=gyn_card, own_only=True)
            gyn_card.reevaluate_card_attrs()


def get_delivery_date_based_on_epicrisis(pregnancy):
    from blueprints.risar.lib.card import PregnancyCard
    if pregnancy.action.has_property('card_number'):
        early_event_id = pregnancy.action.get_prop_value('card_number')
        card = PregnancyCard.get_by_id(early_event_id)
        if card:
            if isinstance(card, PregnancyCard):
                epic = safe_traverse_attrs(card, 'epicrisis', 'action')
                return epic.get_prop_value('delivery_date')