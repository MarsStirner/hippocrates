#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 25.03.2016

"""
from hippocrates.blueprints.risar.models.fetus import RisarFetusState
from nemesis.systemwide import db


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
                if sd_key == 'id':
                    continue
                setattr(fetus_state, sd_key, sd_val)
