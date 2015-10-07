# -*- coding: utf-8 -*-

import datetime
import logging

from collections import defaultdict
from sqlalchemy.orm import aliased

from nemesis.lib.utils import safe_date, safe_int, safe_datetime, safe_bool
from nemesis.systemwide import db
from nemesis.models.actions import Action
from nemesis.models.expert_protocol import (ExpertScheme, ExpertSchemeMKBAssoc, EventMeasure, ExpertProtocol,
    ExpertSchemeMeasureAssoc, rbMeasureType, Measure, MeasureSchedule, rbMeasureScheduleApplyType)
from nemesis.models.exists import MKB
from nemesis.models.enums import MeasureStatus, MeasureScheduleTypeKind
from blueprints.risar.lib.utils import get_event_diag_mkbs
from blueprints.risar.lib.pregnancy_dates import get_pregnancy_start_date
from blueprints.risar.risar_config import first_inspection_code
from blueprints.risar.lib.time_converter import DateTimeUtil
from blueprints.risar.lib.datetime_interval import DateTimeInterval, get_intersection_type, IntersectionType


class EventMeasureController(object):

    def __init__(self):
        pass

    def cancel(self, em):
        em.status = MeasureStatus.cancelled[0]

    def store(self, *em_list):
        db.session.add_all(em_list)
        db.session.commit()