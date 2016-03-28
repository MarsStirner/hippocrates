#! coding:utf-8
"""


@author: Dmitry Paschenko
@date: 25.03.2016

"""
from blueprints.risar.models.fetus import FetusState
from blueprints.risar.models.vesta_props import VestaProperty
from nemesis.systemwide import db


def create_or_update_fetuses(action, fetuses):
    with db.session.no_autoflush:
        for fetuses_data in fetuses:
            deleted = fetuses_data.get('deleted')
            state_data = fetuses_data.get('state')
            fetuse_state_id = state_data and state_data.get('id', None)
            if deleted:
                if fetuse_state_id:
                    FetusState.query.filter(FetusState.id == fetuse_state_id).delete()
            elif state_data:
                if fetuse_state_id:
                    fetus_state = FetusState.query.get(fetuse_state_id)
                else:
                    fetus_state = FetusState(action_id=action.id)
                db.session.add(fetus_state)  # Ничего страшного, если добавим в сессию уже добавленный объект
                for sd_key, sd_val in state_data.items():
                    if isinstance(getattr(fetus_state.__class__, sd_key), VestaProperty):
                        setattr(fetus_state, '_'.join((sd_key, 'code')), sd_val and sd_val['code'])
                    else:
                        setattr(fetus_state, sd_key, sd_val)
