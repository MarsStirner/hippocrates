# -*- coding: utf-8 -*-
from flask_login import current_user

from hippocrates.blueprints.risar.risar_config import first_inspection_flat_code, second_inspection_flat_code, \
    risar_gyn_checkup_flat_code
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, fill_these_attrs_from_action, \
    fill_action_from_another_action
from nemesis.lib.utils import safe_datetime


def copy_checkup(event, from_action):
    flat_code = from_action.actionType.flatCode
    if flat_code in (first_inspection_flat_code, second_inspection_flat_code):
        empty_action = get_action_by_id(None, event, second_inspection_flat_code, True)
        if flat_code == first_inspection_flat_code:
            fields_to_copy_from_prev = ['weight', 'state', 'complaints', 'ad_right_high', 'ad_left_high',
                                        'ad_right_low', 'ad_left_low', 'skin', 'heart_tones', 'breast',
                                        'nipples', 'breathe', 'stomach', 'liver', 'bowel_and_bladder_habits',
                                        'abdominal', 'fundal_height', 'metra_state', 'externalia', 'vagina',
                                        'cervix', 'cervix_length', 'cervix_position', 'cervix_maturity',
                                        'cervix_consistency', 'cervical_canal', 'body_of_womb', 'appendages',
                                        'parametrium', 'features', 'vagina_secretion', 'cervical_canal_secretion',
                                        'urethra_secretion', 'onco_smear', 'pregnancy_week', 'pregnancy_continuation',
                                        'pregnancy_continuation_refusal', 'notes',
                                        'recommendations', 'fetus_first_movement_date', ]
            fill_these_attrs_from_action(from_action=from_action,
                                         to_action=empty_action,
                                         attr_list=fields_to_copy_from_prev)
            empty_action.set_prop_value('lymph_nodes', from_action.get_prop_value('lymph'))
        elif flat_code == second_inspection_flat_code:
            fill_action_from_another_action(from_action=from_action,
                                            to_action=empty_action, exclude_attr_list=["next_date"])
        return empty_action


def copy_gyn_checkup(event, from_action):
    flat_code = from_action.actionType.flatCode
    if flat_code != risar_gyn_checkup_flat_code:
        return

    empty_action = get_action_by_id(None, event, flat_code, True)
    fill_action_from_another_action(from_action=from_action,
                                    to_action=empty_action)
    return empty_action


def can_read_checkup(action):
    return True


def can_edit_checkup(action):
    return current_user.has_right('adm') or (
        action.setPerson_id == current_user.id and
        action.endDate is None
    )


def get_checkup_interval(action, args=None):
    if args is None:
        args = {}
    start_date = safe_datetime(action.begDate)
    end_date = safe_datetime(action.get_prop_value('next_date'))
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        end_date = action.endDate
    args.update({
        'event_id': action.event_id,
        'end_date_from': start_date,
        'action_id': action.id
    })
    if end_date:
        args['beg_date_to'] = end_date
    return args


def validate_send_to_mis_checkup(checkup):
    # from nemesis.models.diagnosis import Action_Diagnosis, rbDiagnosisKind, \
    #     rbDiagnosisTypeN, Diagnostic
    # from nemesis.systemwide import db
    res = True
    talon25 = checkup.propsByCode['ticket_25'].value
    # dg_q = Action_Diagnosis.query.join(
    #     rbDiagnosisKind
    # ).join(
    #     rbDiagnosisTypeN
    # ).join(
    #     Diagnostic, Diagnostic.action == checkup
    # ).filter(
    #     Diagnostic.diagnosis_id == Action_Diagnosis.diagnosis_id,
    #     Action_Diagnosis.deleted == 0,
    #     Action_Diagnosis.action == checkup,
    #     rbDiagnosisKind.code == 'main',
    #     rbDiagnosisTypeN.code == 'final',
    #     Diagnostic.rbAcheResult_id.isnot(None),
    # )

    if not talon25.propsByCode['medical_care'].value:
        res = False
    elif not talon25.propsByCode['visit_place'].value:
        res = False
    elif not talon25.propsByCode['visit_reason'].value:
        res = False
    elif not talon25.propsByCode['visit_type'].value:
        res = False
    elif not talon25.propsByCode['finished_treatment'].value:
        res = False
    elif not talon25.propsByCode['initial_treatment'].value:
        res = False
    elif not talon25.propsByCode['treatment_result'].value:
        res = False
    elif not talon25.propsByCode['payment'].value:
        res = False
    elif not talon25.propsByCode['prof_med_help'].value:
        res = False
    elif not talon25.propsByCode['condit_med_help'].value:
        res = False
    elif not talon25.propsByCode['ache_result'].value:
        res = False
    elif not talon25.propsByCode['services'].value:
        res = False
    # elif not db.session.query(dg_q.exists()).scalar():
    #     res = False
    return res
