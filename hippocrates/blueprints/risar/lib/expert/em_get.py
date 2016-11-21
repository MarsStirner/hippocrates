# coding: utf-8

import datetime
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased, joinedload

from nemesis.models.expert_protocol import EventMeasure, ExpertSchemeMeasureAssoc, Measure
from nemesis.systemwide import db


def get_latest_measures_in_event(event_id, upto_date=None, with_result=False):
    """Самые последние мероприятия случая на дату upto_date или текущую дату.

    По одному EventMeasure на каждый тип мероприятия Measure.
    При этом берутся как автоматически созданные мероприятия на основе схем
    (schemeMeasure_id is not null), так и создаваемые вручную (measure_id is not null).
    """
    if not upto_date:
        upto_date = datetime.date.today()
    elif isinstance(upto_date, datetime.datetime):
        upto_date = upto_date.date()

    UserMeasure = aliased(Measure, name='UserMeasure')
    base_query = db.session.query(EventMeasure).outerjoin(
        ExpertSchemeMeasureAssoc, Measure
    ).outerjoin(
        UserMeasure, EventMeasure.measure_id == UserMeasure.id
    ).filter(
        EventMeasure.event_id == event_id,
        EventMeasure.deleted == 0,
        func.date(EventMeasure.begDateTime) <= upto_date
    )
    if with_result:
        base_query = base_query.filter(EventMeasure.resultAction_id.isnot(None))

    latest_measures_dates = base_query.group_by(
        func.IF(EventMeasure.schemeMeasure_id.isnot(None), Measure.id, UserMeasure.id)
    ).with_entities(
        func.max(EventMeasure.begDateTime).label('max_date'),
        func.IF(EventMeasure.schemeMeasure_id.isnot(None), Measure.id, UserMeasure.id).label('measure_id')
    ).subquery('LatestMeasuresDates')

    latest_measures_ids = base_query.join(
        latest_measures_dates, and_(EventMeasure.begDateTime == latest_measures_dates.c.max_date,
                                    func.IF(EventMeasure.schemeMeasure_id.isnot(None),
                                            Measure.id,
                                            UserMeasure.id) == latest_measures_dates.c.measure_id)
    ).group_by(
        func.IF(EventMeasure.schemeMeasure_id.isnot(None), Measure.id, UserMeasure.id)
    ).with_entities(
        func.max(EventMeasure.id).label('em_id'),
        func.IF(EventMeasure.schemeMeasure_id.isnot(None), Measure.id, UserMeasure.id).label('measure_id')
    ).subquery('LatestMeasuresIds')

    latest_measures = db.session.query(EventMeasure).join(
        latest_measures_ids, EventMeasure.id == latest_measures_ids.c.em_id
    ).options(
        joinedload(EventMeasure._scheme_measure).joinedload('measure', innerjoin=True),
        joinedload(EventMeasure._measure),
    ).all()

    return latest_measures