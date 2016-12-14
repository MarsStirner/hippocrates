# -*- coding: utf-8 -*-

from hippocrates.blueprints.risar.risar_config import risar_anamnesis_pregnancy
from hippocrates.blueprints.risar.lib.utils import fill_action_from_another_action, get_action_by_id
from hippocrates.blueprints.risar.models.risar import RisarEpicrisis_Children, RisarPreviousPregnancy_Children
from nemesis.systemwide import db
from nemesis.lib.utils import safe_traverse


def copy_anamnesis_from_gyn_card(gyn_card, preg_card):
    preg_card.anamnesis.mother['menstruation_start_age'].value = gyn_card.anamnesis['age'].value
    preg_card.anamnesis.mother['menstruation_duration'].value = gyn_card.anamnesis['duration'].value
    preg_card.anamnesis.mother['menstruation_period'].value = gyn_card.anamnesis['period_duration'].value
    preg_card.anamnesis.mother['menstruation_disorders'].value = gyn_card.anamnesis['disorder'].value
    preg_card.anamnesis.mother['sex_life_start_age'].value = gyn_card.anamnesis['sex_life_age'].value
    preg_card.anamnesis.mother['marital_status'].value = gyn_card.anamnesis['marital_status'].value
    preg_card.anamnesis.mother['infertility'].value = gyn_card.anamnesis['infertility'].value
    preg_card.anamnesis.mother['infertility_type'].value = gyn_card.anamnesis['infertility_kind'].value
    preg_card.anamnesis.mother['infertility_period'].value = gyn_card.anamnesis['infertility_duration'].value
    preg_card.anamnesis.mother['infertility_cause'].value = gyn_card.anamnesis['infertility_etiology'].value
    preg_card.anamnesis.mother['infertility_treatment'].value = gyn_card.anamnesis['infertility_treatment'].value
    preg_card.anamnesis.mother['alcohol'].value = gyn_card.anamnesis['alcohol'].value
    preg_card.anamnesis.mother['smoking'].value = gyn_card.anamnesis['smoking'].value
    preg_card.anamnesis.mother['toxic'].value = gyn_card.anamnesis['toxic'].value
    preg_card.anamnesis.mother['drugs'].value = gyn_card.anamnesis['drugs'].value
    preg_card.anamnesis.mother['work_group'].value = gyn_card.anamnesis['work_group'].value
    preg_card.anamnesis.mother['professional_properties'].value = gyn_card.anamnesis['professional_properties'].value


def calculate_preg_result(epicrisis):
    pregnancy_final = safe_traverse(epicrisis['pregnancy_final'].value, 'code')
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
        abort_kind = epicrisis['abort'].value.get('code')
        if abort_kind == "samoproizvol_nyj":
            if pregnancy_duration < 11:
                code = "misbirth_before_11"
            elif 12 <= pregnancy_duration <= 21:
                code = "misbirth_before_12-21"
        elif abort_kind in ["'abortmedikamentoznymmetodom-posostoaniurebenka",
                            'abortmedikamentoznymmetodom-posostoaniujensiny',
                            'iskusstvennyj-pomed.pokazaniamjensiny',
                            'iskusstvennyj-pomed.pokazaniamploda',
                            ]:
            code = "delivery"
    if code:
        return {"code": code}


def create_prev_pregn_based_on_epicrisis(from_card, to_card):
    epic_props = from_card.epicrisis.action
    blank_action = get_action_by_id(None, to_card.event, risar_anamnesis_pregnancy, True)
    blank_action['year'].value = epic_props['delivery_date'].value.year if epic_props[
        'delivery_date'].value else None
    blank_action['pregnancyResult'].value = calculate_preg_result(epic_props)
    blank_action['pregnancy_week'].value = epic_props['pregnancy_duration'].value
    blank_action['maternity_aid'].value = [{'code': '05'}] if epic_props['caesarean_section'].value else None
    blank_action['operation_testimonials'].value = epic_props['indication'].value
    if not blank_action['card_number'].value:
        blank_action['card_number'].value = from_card.event.id
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


def copy_all_prev_pregs(from_card, to_card):
    prev_pregs = from_card.prev_pregs
    for prev in prev_pregs:
        empty_action = get_action_by_id(None, to_card.event, risar_anamnesis_pregnancy, True)
        fill_action_from_another_action(prev.action, empty_action)
        if not empty_action['card_number'].value:
            empty_action['card_number'].value = from_card.event.id
        db.session.add(empty_action)
        for nb in RisarPreviousPregnancy_Children.query.filter(
                        RisarPreviousPregnancy_Children.action_id == prev.action.id
        ).all():
            child = RisarPreviousPregnancy_Children()
            child.action_id = empty_action.id
            child.weight = nb.weight
            child.alive = nb.alive
            child.sex = nb.sex
            db.session.add(child)