#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 25.03.2016

"""
from blueprints.risar.models.fetus import RisarFetusState
from nemesis.systemwide import db
from nemesis.models.enums import FisherKTGRate
from nemesis.lib.utils import safe_traverse


def create_or_update_fetuses(action, fetuses):
    for fetuses_data in fetuses:
        deleted = fetuses_data.get('deleted')
        state_data = fetuses_data.get('state')
        fetuse_state_id = state_data and state_data.get('id', None)
        if deleted:
            if fetuse_state_id:
                RisarFetusState.query.filter(RisarFetusState.id == fetuse_state_id).delete()
        elif state_data:
            if fetuse_state_id:
                fetus_state = RisarFetusState.query.get(fetuse_state_id)
            else:
                fetus_state = RisarFetusState(action=action, action_id=action.id)
            db.session.add(fetus_state)  # Ничего страшного, если добавим в сессию уже добавленный объект
            for sd_key, sd_val in state_data.items():
                if sd_key == 'id' or sd_key == 'fisher_ktg_rate':
                    continue
                setattr(fetus_state, sd_key, sd_val)
            points, rate = calc_fisher_ktg_info(state_data)
            fetus_state.fisher_ktg_points = points
            fetus_state.fisher_ktg_rate_id = rate.value if rate else None


def calc_fisher_ktg_info(fetus_data):
    ktg_enabled = fetus_data.get('ktg_input') or False
    if not ktg_enabled:
        return None, None

    total_points = 0
    if 'basal' in fetus_data:
        basal_code = safe_traverse(fetus_data, 'basal', 'code')
        if basal_code == '03':  # 120 <= basal <= 160
            total_points += 2
        elif basal_code in ('02', '04'):  # 100 <= basal < 120 or 160 < basal <= 180
            total_points += 1
    if 'variability_range' in fetus_data:
        variability_range_code = safe_traverse(fetus_data, 'variability_range', 'code')
        if variability_range_code == '02':  # 3 <= x <= 5
            total_points += 1
        elif variability_range_code == '03':  # 5 < x <=25
            total_points += 2
    if 'frequency_per_minute' in fetus_data:
        frequency_per_minute_code = safe_traverse(fetus_data, 'frequency_per_minute', 'code')
        if frequency_per_minute_code == '02':  # 3 <= x <= 5
            total_points += 1
        elif frequency_per_minute_code == '03':  # 6 <= x
            total_points += 2
    if 'acceleration' in fetus_data:
        acceleration_code = safe_traverse(fetus_data, 'acceleration', 'code')
        if acceleration_code == '02':  # 1 <= x <= 4
            total_points += 1
        elif acceleration_code == '03':  # 5 <= x
            total_points += 2
    if 'deceleration' in fetus_data:
        deceleration_code = safe_traverse(fetus_data, 'deceleration', 'code')
        if deceleration_code == '02':  # легкие и среднетяжелые
            total_points += 1
        elif deceleration_code == '03':  # отсутствие или короткие неглубокие
            total_points += 2

    risk_rate = None
    if 8 <= total_points <= 10:
        risk_rate = FisherKTGRate(FisherKTGRate.normality[0])
    elif 6 <= total_points <= 7:
        risk_rate = FisherKTGRate(FisherKTGRate.prepathological[0])
    elif total_points < 6:
        risk_rate = FisherKTGRate(FisherKTGRate.attention_required[0])

    return total_points, risk_rate


def get_fetuses(action_id):
    if not action_id:
        return []
    return RisarFetusState.query.filter(
        RisarFetusState.action_id == action_id,
        RisarFetusState.deleted == 0,
    ).order_by(RisarFetusState.id).all()
