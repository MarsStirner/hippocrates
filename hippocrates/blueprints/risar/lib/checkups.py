# -*- coding: utf-8 -*-
from flask_login import current_user

from hippocrates.blueprints.risar.risar_config import first_inspection_flat_code, second_inspection_flat_code
from hippocrates.blueprints.risar.lib.utils import get_action_by_id, fill_these_attrs_from_action, \
    fill_action_from_another_action


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
                                        'pregnancy_continuation_refusal', 'next_date', 'notes',
                                        'recommendations', 'fetus_first_movement_date']
            fill_these_attrs_from_action(from_action=from_action,
                                         to_action=empty_action,
                                         attr_list=fields_to_copy_from_prev)
        elif flat_code == second_inspection_flat_code:
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
