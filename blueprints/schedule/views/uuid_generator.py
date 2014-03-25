# -*- coding: utf-8 -*-

import uuid

from application.database import db
from blueprints.schedule.models.exists import UUID


def getNewUUID_id():
    """
    Сгенерировать и записать в таблицу UUID новый уникальный id
    и вернуть id записи
    """

    newUUID = str(uuid.uuid4())
    
    record = UUID()
    record.uuid = newUUID
    
    id_ = None
    while id_ is None:
        try:
            db.session.add(record)
            db.session.commit()
            id_ = record.id
        except:
            raise
            continue
        
    return id_
