# -*- coding: utf-8 -*-

import logging

from ..xform import XForm, wrap_simplify, VALIDATION_ERROR
from .schemas import MeasureListSchema

from blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from blueprints.risar.lib.expert.utils import em_cancelled_all, em_status_all

from nemesis.lib.apiutils import ApiException
from nemesis.lib.utils import safe_date
from nemesis.models.event import Event
from nemesis.models.enums import MeasureStatus


logger = logging.getLogger('simple')


class MeasureListXForm(MeasureListSchema, XForm):
    target_id_required = False
    parent_obj_class = Event

    def __init__(self, *args, **kwargs):
        XForm.__init__(self, *args, **kwargs)
        self.measure_list = []

    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        pass

    def load_data(self, args):
        if 'date_begin' in args:
            date_begin = safe_date(args['date_begin'])
            if not date_begin:
                raise ApiException(
                    VALIDATION_ERROR,
                    u'Аргумент date_begin не соответствует формату даты YYYY-MM-DD'
                )
            args['date_begin'] = date_begin
        if 'date_end' in args:
            date_end = safe_date(args['date_end'])
            if not date_end:
                raise ApiException(
                    VALIDATION_ERROR,
                    u'Аргумент date_end не соответствует формату даты YYYY-MM-DD'
                )
            args['date_end'] = date_end
        self.measure_list = self._get_measure_list(event_id=self.parent_obj_id, **args)

    def _get_measure_list(self, **kwargs):
        event_id = kwargs['event_id']
        flt = {
            'event_id': event_id,
            'measure_status_id_list': em_status_all - em_cancelled_all
        }
        if 'date_begin' in kwargs:
            kwargs['end_date_from'] = kwargs['date_begin']
        if 'date_end' in kwargs:
            flt['beg_date_to'] = kwargs['date_end']
        em_ctrl = EventMeasureController()
        data = em_ctrl.get_measures_in_event(None, flt)
        return data

    @wrap_simplify
    def as_json(self):
        return map(self._represent_measure, self.measure_list)

    def _represent_measure(self, measure):
        dc = {
            'measure_id': measure.id,
            'measure_type_code': measure.measure.code,
            'begin_datetime': safe_date(measure.begDateTime),
            'end_datetime': safe_date(measure.endDateTime),
            'status': unicode(MeasureStatus(measure.status)),
            'result_action_id': self.or_undefined(measure.resultAction_id),
            'indications': ''
        }
        try:
            dc['indications'] = measure.scheme_measure.schedule.additionalText
        except Exception as e:
            #blank indications
            pass

        return dc
