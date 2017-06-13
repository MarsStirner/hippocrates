# -*- coding: utf-8 -*-

import logging

from nemesis.models.expert_protocol import rbMeasureStatus, Measure, \
    rbMeasureType
from ..xform import XForm, wrap_simplify, VALIDATION_ERROR
from .schemas import MeasureListSchema, MeasureSchema

from hippocrates.blueprints.risar.lib.expert.em_manipulation import EventMeasureController
from hippocrates.blueprints.risar.lib.expert.utils import em_cancelled_all, em_status_all

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
        self.measure = None

    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        pass

    def load_data(self, args=None):
        if self.target_obj_id:
            self.measure = self._get_measure()
        else:
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

    def _get_measure(self):
        em_ctrl = EventMeasureController()
        data = em_ctrl.get_measure(self.target_obj_id)
        return data

    def _get_measure_list(self, **kwargs):
        event_id = kwargs['event_id']
        flt = {
            'event_id': event_id,
            'measure_status_id_list': em_status_all - em_cancelled_all
        }
        if 'date_begin' in kwargs:
            # em.endDateTime >= date_begin
            flt['end_date_from'] = kwargs['date_begin']
        if 'date_end' in kwargs:
            # em.begDateTime <= date_end
            flt['beg_date_to'] = kwargs['date_end']
        em_ctrl = EventMeasureController()
        # Если заданы date_begin и date_end, то будут выбраны все мероприятия, которые попадают в этот диапазон
        # полностью или частично.
        data = em_ctrl.get_measures_in_event(None, flt)
        return data

    def update_target_obj(self, data):
        event = None
        measure_id = Measure.query.filter(
            Measure.regionalCode == data['measure_type_code'],
            Measure.resultAt_id.isnot(None),
        ).first().id
        em_ctrl = EventMeasureController()
        em_data = [{
            'id': data.get('measure_id'),
            'data': {
                'beg_datetime': data['begin_datetime'],
                'end_datetime': data['end_datetime'],
                'event_id': self.parent_obj_id,
                'measure_id': measure_id,
                'status': {'id': self.rb_validate(rbMeasureStatus, data['status'], 'regionalCode')[0]},
            }
        }]
        em_list = em_ctrl.save_list(event, em_data)
        em_ctrl.store(*em_list)
        self.measure = em_list[0]

    @wrap_simplify
    def as_json(self):
        measure = self.measure or self.measure_list
        if isinstance(measure, list):
            return map(self._represent_measure, measure)
        else:
            return self._represent_measure(measure)

    def _represent_measure(self, measure):
        dc = {
            'measure_id': measure.id,
            'measure_type_code': measure.measure.regionalCode,
            'begin_datetime': safe_date(measure.begDateTime),
            'end_datetime': safe_date(measure.endDateTime),
            'status': unicode(MeasureStatus(measure.status)),
            'result_action_id': self.or_undefined(measure.resultAction_id),
            'indications': '',
            'appointment_id': measure.appointmentAction_id,
        }
        try:
            dc['indications'] = measure.scheme_measure.schedule.additionalText
        except Exception as e:
            # blank indications
            pass

        return dc


class MeasureXForm(MeasureSchema, MeasureListXForm):
    pass
