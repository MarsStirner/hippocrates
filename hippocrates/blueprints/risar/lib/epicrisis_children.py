#! coding:utf-8
"""


@author: BARS Group
@date: 19.04.2016

"""
from blueprints.risar.models.risar import RisarEpicrisis_Children
from nemesis.systemwide import db


def create_or_update_newborns(action, newborns):
    for newborn_data in newborns:
        deleted = newborn_data.get('deleted')
        newborn_id = newborn_data and newborn_data.get('id', None)
        if deleted:
            if newborn_id:
                RisarEpicrisis_Children.query.filter(RisarEpicrisis_Children.id == newborn_id).delete()
        elif newborn_data:
            if newborn_id:
                epicrisis_newborn = RisarEpicrisis_Children.query.get(newborn_id)
            else:
                epicrisis_newborn = RisarEpicrisis_Children(action=action, action_id=action.id)
            db.session.add(epicrisis_newborn)  # Ничего страшного, если добавим в сессию уже добавленный объект
            for sd_key, sd_val in newborn_data.items():
                if sd_key == 'sex':
                    setattr(epicrisis_newborn, sd_key, sd_val)
                else:
                    setattr(epicrisis_newborn, sd_key, 1 if sd_val == 'male' else 2)
