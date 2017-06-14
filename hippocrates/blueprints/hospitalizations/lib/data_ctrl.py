# -*- coding: utf-8 -*-

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import aliased, contains_eager, joinedload

from hippocrates.blueprints.event.lib.utils import get_hb_days_for_moving_list
from nemesis.lib.utils import safe_int, safe_traverse
from nemesis.lib.const import STATIONARY_EVENT_CODES, STATIONARY_MOVING_CODE, \
    STATIONARY_RECEIVED_CODE, STATIONARY_ORG_STRUCT_STAY_CODE, \
    STATIONARY_ORG_STRUCT_TRANSFER_CODE, STATIONARY_HOSP_BED_CODE, \
    STATIONARY_LEAVED_CODE
from nemesis.models.enums import HospStateStatus
from nemesis.lib.data_ctrl.base import BaseSelecter, BaseModelController
from nemesis.lib.diagnosis import get_events_diagnoses, format_diagnoses


class HospitalizationController(BaseModelController):

    def get_hosps(self, start_dt, end_dt, history, **kwargs):
        sel = HospitalizationSelector()
        hosps_data = sel.get_latest_hosps(start_dt, end_dt, history, **kwargs)

        event_id_list = [hosp.Event.id for hosp in hosps_data.items]
        diag_data = get_events_diagnoses(event_id_list)
        diag_data = format_diagnoses(diag_data)

        moving_ids = [hosp.moving_id for hosp in hosps_data.items]
        hb_days_data = get_hb_days_for_moving_list(moving_ids)

        hosp_list = []
        for hosp in hosps_data.items:
            h = {
                'id': hosp.Event.id,
                'external_id': hosp.Event.externalId,
                'exec_person': {
                    'id': hosp.Event.execPerson_id,
                    'short_name': hosp.Event.execPerson.shortNameText if hosp.Event.execPerson else ''
                },
                'client': {
                    'id': hosp.Event.client.id,
                    'full_name': hosp.Event.client.nameText,
                    'birth_date': hosp.Event.client.birthDate,
                    'age': hosp.Event.client.age
                },
                'moving': {
                    'id': hosp.moving_id,
                    'end_date': hosp.moving_end_date
                },
                'received': {
                    'id': hosp.received_id
                },
                'move_date': hosp.move_date,
                'org_struct_name': hosp.os_name,
                'hosp_bed_name': hosp.hosp_bed_name,
                'diagnoses': diag_data.get(hosp.Event.id),
                'hb_days': safe_traverse(hb_days_data, hosp.Event.id, 'hb_days')
            }
            hosp_list.append(h)
        return {
            'items': hosp_list,
            'count': hosps_data.total,
            'total_pages': hosps_data.pages
        }

    def get_hosps_stats(self, start_dt, end_dt, history, **kwargs):
        sel = HospitalizationSelector()
        stats1 = sel.get_hosps_status_counts(start_dt, end_dt, history, **kwargs)
        stats2 = sel.get_hosps_status_counts(start_dt, start_dt, True,
                                             statuses=[HospStateStatus.current[0]], **kwargs)
        stats3 = sel.get_hosps_by_doctor_counts(start_dt, end_dt, history, **kwargs)
        by_doctors = dict(
            (person.id,
             {
                 'person_name': person.shortNameText,
                 'events_count': cnt or 0
             })
            for person, cnt in stats3
        )
        return {
            'count_current': stats1.count_current or 0,
            'count_received': stats1.count_received or 0,
            'count_transferred': stats1.count_transferred or 0,
            'count_leaved': stats1.count_leaved or 0,
            'count_current_prev_day': stats2.count_current or 0,
            'count_current_by_doctor': by_doctors
        }


class HospitalizationSelector(BaseSelecter):

    def __init__(self, query=None):
        Action = self.model_provider.get('Action')
        OrgStructure = self.model_provider.get('OrgStructure')
        OrgStructure_HospitalBed = self.model_provider.get('OrgStructure_HospitalBed')

        self.BaseEvent = self.model_provider.get('Event')
        self.MovingAction = aliased(Action, name='LatestMovingAction')
        self.ReceivedAction = aliased(Action, name='ReceivedAction')
        self.LeavedAction = aliased(Action, name='LeavedAction')
        self.LocationOSfromMoving = aliased(OrgStructure, name='LocationOrgStructFromMoving')
        self.LocationOSfromReceived = aliased(OrgStructure, name='LocationOrgStructFromReceived')
        self.MovingOSHB = aliased(OrgStructure_HospitalBed, name='MovingHospitalBed')
        self.MovingOrgStructTransfer = aliased(OrgStructure, name='MovingOrgStructTransfer')
        self.q_movings_transfered_through = None

        self.start_dt = None
        self.end_dt = None
        self.hosp_status = None
        self.flt_org_struct_id = None
        self.history = None
        self._latest_location_joined = False
        self._location_os_joined = False
        self._leaved_joined = False
        self._moving_os_transfer_joined = False
        self._moving_transfer_through_joined = False
        super(HospitalizationSelector, self).__init__(query)

    def set_base_query(self):
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        Client = self.model_provider.get('Client')

        self.query = self.session.query(self.BaseEvent).join(
            Client, EventType, rbRequestType
        ).filter(
            self.BaseEvent.deleted == 0, self.BaseEvent.execDate.is_(None),
            rbRequestType.code.in_(STATIONARY_EVENT_CODES),
        )
        self._latest_location_joined = False
        self._location_os_joined = False
        self._leaved_joined = False
        self._moving_os_transfer_joined = False
        self.q_movings_transfered_through = None
        self._moving_transfer_through_joined = False

    def get_latest_hosps(self, start_dt, end_dt, history, **kwargs):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.history = history
        self.hosp_status = safe_int(kwargs.get('hosp_status'))
        self.flt_org_struct_id = safe_int(kwargs.get('org_struct_id'))

        self.set_base_query()
        self._filter_by_latest_location()
        self._filter_by_status()
        self._join_location_org_structure()
        self._join_hosp_bed()

        self.query = self.query.with_entities(
            self.BaseEvent,
            self.MovingAction.id.label('moving_id'),
            self.ReceivedAction.id.label('received_id'),
            func.IF(self.MovingAction.id.isnot(None),
                    self.MovingAction.begDate,
                    self.ReceivedAction.begDate).label('move_date'),
            self.MovingAction.endDate.label('moving_end_date'),
            func.IF(self.MovingAction.id.isnot(None),
                    self.LocationOSfromMoving.name,
                    self.LocationOSfromReceived.name).label('os_name'),
            self.MovingOSHB.name.label('hosp_bed_name'),
        )
        self.query = self.query.order_by(
            func.IF(self.MovingAction.id.isnot(None),
                    self.MovingAction.begDate,
                    self.ReceivedAction.begDate).desc()
        )

        self.query = self.query.options(
            contains_eager(self.BaseEvent.client),
            joinedload(self.BaseEvent.execPerson)
        )
        return self.get_paginated(kwargs)

    def get_hosps_status_counts(self, start_dt, end_dt, history, **kwargs):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.history = history
        self.hosp_status = safe_int(kwargs.get('hosp_status'))
        self.flt_org_struct_id = safe_int(kwargs.get('org_struct_id'))

        statuses = set(kwargs.get('statuses') or HospStateStatus.get_values())

        self.set_base_query()
        self._join_latest_location()
        self._join_location_org_structure()
        self._join_moving_os_transfer()
        self._join_movings_transfered_through()
        self._join_leaved()

        self.query = self.query.filter(
            or_(self.MovingAction.id.isnot(None),
                self.ReceivedAction.id.isnot(None)),
        ).with_entities()
        if HospStateStatus.current[0] in statuses:
            # кол-во текущих
            self.query = self.query.add_column(
                func.SUM(
                    func.IF(func.IF(self.MovingAction.id.isnot(None),
                                    and_(self.MovingAction.begDate < self.end_dt,
                                         or_(self.MovingAction.endDate.is_(None),
                                             self.end_dt <= self.MovingAction.endDate),
                                         func.IF(self.flt_org_struct_id is not None,
                                                 self.LocationOSfromMoving.id == self.flt_org_struct_id,
                                                 1)
                                         ),
                                    and_(self.ReceivedAction.begDate < self.end_dt,
                                         or_(self.ReceivedAction.endDate.is_(None),
                                             self.end_dt <= self.ReceivedAction.endDate),
                                         func.IF(self.flt_org_struct_id is not None,
                                                 self.LocationOSfromReceived.id == self.flt_org_struct_id,
                                                 1)
                                         )),
                            1, 0)
                ).label('count_current')
            )

        if HospStateStatus.received[0] in statuses:
            # кол-во поступивших
            self.query = self.query.add_column(
                func.SUM(
                    func.IF(func.IF(self.MovingAction.id.isnot(None),
                                    and_(self.MovingAction.begDate < self.end_dt,
                                         self.start_dt <= self.MovingAction.begDate,
                                         or_(self.MovingAction.endDate.is_(None),
                                             self.start_dt <= self.MovingAction.endDate),
                                         func.IF(self.flt_org_struct_id is not None,
                                                 self.LocationOSfromMoving.id == self.flt_org_struct_id,
                                                 1)
                                         ),
                                    and_(self.ReceivedAction.begDate < self.end_dt,
                                         self.start_dt <= self.ReceivedAction.begDate,
                                         or_(self.ReceivedAction.endDate.is_(None),
                                             self.start_dt <= self.ReceivedAction.endDate),
                                         func.IF(self.flt_org_struct_id is not None,
                                                 self.LocationOSfromReceived.id == self.flt_org_struct_id,
                                                 1)
                                         )
                                    ),
                            1, 0)
                ).label('count_received')
            )

        if HospStateStatus.transferred[0] in statuses:
            # кол-во переведенных
            self.query = self.query.add_column(
                func.SUM(
                    func.IF(self.q_movings_transfered_through.c.event_id.isnot(None),
                            1, 0)
                ).label('count_transferred')
            )

        if HospStateStatus.leaved[0] in statuses:
            # кол-во выписанных
            self.query = self.query.add_column(
                func.SUM(
                    func.IF(and_(self.LeavedAction.id.isnot(None),
                                 self.MovingOrgStructTransfer.id.is_(None),
                                 self.MovingAction.begDate < self.end_dt,
                                 self.MovingAction.endDate >= self.start_dt,
                                 self.MovingAction.endDate < self.end_dt),
                            1, 0)
                ).label('count_leaved')
            )

        return self.get_one()

    def get_hosps_by_doctor_counts(self, start_dt, end_dt, history, **kwargs):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.history = history
        self.hosp_status = HospStateStatus.current[0]
        self.flt_org_struct_id = safe_int(kwargs.get('org_struct_id'))

        self.set_base_query()
        self._join_latest_location()
        self._filter_by_status()

        Person = self.model_provider.get('Person')

        self.query = self.query.join(
            Person, self.BaseEvent.execPerson_id == Person.id
        ).group_by(
            self.BaseEvent.execPerson_id
        ).with_entities(
            Person,
            func.count(self.BaseEvent.id.distinct()).label('count_events')
        )

        return self.get_all()

    def _filter_by_latest_location(self):
        self._join_latest_location()
        if not self.history:
            self.query = self.query.filter(
                func.IF(self.MovingAction.id.isnot(None),
                        # движение попадает во временной интервал
                        and_(self.MovingAction.begDate < self.end_dt,
                             or_(self.MovingAction.endDate.is_(None),
                                 self.start_dt <= self.MovingAction.endDate)
                             ),
                        # поступление попадает во временной интервал
                        and_(self.ReceivedAction.begDate < self.end_dt,
                             or_(self.ReceivedAction.endDate.is_(None),
                                 self.start_dt <= self.ReceivedAction.endDate)
                             )
                        )
            )

    def _filter_by_status(self):
        if self.hosp_status == HospStateStatus.transferred[0]:
            # Переведенные - Action.endDate между beg_date и end_date, а поле "Переведен в отделение"
            # не пустое, отделение пребывания равно текущему отделению пользователя;
            self._join_movings_transfered_through()
            self.query = self.query.filter(
                self.q_movings_transfered_through.c.event_id.isnot(None)
            )
        else:
            self.query = self.query.filter(
                or_(self.MovingAction.id.isnot(None),
                    self.ReceivedAction.id.isnot(None)),
            )
            self._filter_by_location_os()

            # Текущие - Action.endDate для движения пусто или больше end_date,
            # отделение пребывания равно текущему отделению пользователя. Плюс отображаем пациентов, у которых есть
            # поступление в это отделение, но их еще не разместили на койке (в таком случае, у этих пациентов в столбце
            # "Койка" будет отображаться гиперссылка "Положить на койку").
            if self.hosp_status == HospStateStatus.current[0]:
                self.query = self.query.filter(
                    func.IF(self.MovingAction.id.isnot(None),
                            or_(self.MovingAction.endDate.is_(None),
                                self.MovingAction.endDate >= self.end_dt),
                            or_(self.ReceivedAction.endDate.is_(None),
                                self.ReceivedAction.endDate >= self.end_dt)
                            )
                )
            # Поступившие - Action.begDate для движения более или равно beg_date, а endDate любая, отделение
            # пребывания равно текущему отделению пользователя;
            elif self.hosp_status == HospStateStatus.received[0]:
                self.query = self.query.filter(
                    func.IF(self.MovingAction.id.isnot(None),
                            and_(self.MovingAction.begDate >= self.start_dt,
                                 self.MovingAction.begDate <= self.end_dt),
                            and_(self.ReceivedAction.begDate >= self.start_dt,
                                 self.ReceivedAction.begDate <= self.end_dt),
                            )
                )
            # Выписанные - Action.endDate между beg_date и end_date, а поле "Переведен в отделение" пусто. Присутствует
            # "Выписной эпикриз" - но необязательно для того, чтобы считать пациента убывшим из отделения.
            elif self.hosp_status == HospStateStatus.leaved[0]:
                self._join_leaved()
                self._join_moving_os_transfer()

                self.query = self.query.filter(
                    self.LeavedAction.id.isnot(None),
                    self.MovingOrgStructTransfer.id.is_(None),
                    and_(self.MovingAction.endDate >= self.start_dt,
                         self.MovingAction.endDate < self.end_dt)
                )

    def _join_latest_location(self):
        if self._latest_location_joined:
            return

        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')

        q_latest_moving = self.session.query(Action.id.label('action_id')).join(
            ActionType
        ).filter(
            Action.event_id == self.BaseEvent.id,
            ActionType.flatCode == STATIONARY_MOVING_CODE,
            Action.deleted == 0
        ).order_by(
            Action.begDate.desc()
        )
        if self.history:
            # движение попадает во временной интервал
            q_latest_moving = q_latest_moving.filter(
                Action.begDate < self.end_dt,
                or_(Action.endDate.is_(None),
                    Action.endDate >= self.start_dt)
            )
        q_latest_moving = q_latest_moving.limit(1)

        q_received = self.session.query(Action.id.label('action_id')).join(
            ActionType
        ).filter(
            Action.event_id == self.BaseEvent.id,
            ActionType.flatCode == STATIONARY_RECEIVED_CODE,
            Action.deleted == 0
        ).order_by(
            Action.begDate.desc()
        )
        if self.history:
            # поступление попадает во временной интервал
            q_received = q_received.filter(
                Action.begDate < self.end_dt,
                or_(Action.endDate.is_(None),
                    Action.endDate >= self.start_dt)
            )
        q_received = q_received.limit(1)

        self.query = self.query.outerjoin(
            self.MovingAction, self.MovingAction.id == q_latest_moving
        ).outerjoin(
            self.ReceivedAction, self.ReceivedAction.id == q_received
        )
        self._latest_location_joined = True

    def _join_location_org_structure(self):
        if self._location_os_joined:
            return

        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_OrgStructure = self.model_provider.get('ActionProperty_OrgStructure')
        AP_OS_Moving = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving')
        AP_OS_Received = aliased(ActionProperty_OrgStructure, name='AP_OS_Received')

        q_os_stay_sq = self.session.query(ActionProperty.id)\
            .join(ActionPropertyType)\
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                    ActionProperty.action_id == self.MovingAction.id)\
            .limit(1)
        q_os_transfer_sq = self.session.query(ActionProperty.id)\
            .join(ActionPropertyType)\
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                    ActionProperty.action_id == self.ReceivedAction.id)\
            .limit(1)

        self.query = self.query.outerjoin(
            AP_OS_Moving, AP_OS_Moving.id == q_os_stay_sq
        ).outerjoin(
            self.LocationOSfromMoving, self.LocationOSfromMoving.id == AP_OS_Moving.value_
        ).outerjoin(
            AP_OS_Received, AP_OS_Received.id == q_os_transfer_sq
        ).outerjoin(
            self.LocationOSfromReceived, self.LocationOSfromReceived.id == AP_OS_Received.value_
        )
        self._location_os_joined = True

    def _filter_by_location_os(self):
        if self.flt_org_struct_id is not None:
            self._join_location_org_structure()
            self.query = self.query.filter(
                func.IF(self.MovingAction.id.isnot(None),
                        self.LocationOSfromMoving.id == self.flt_org_struct_id,
                        self.LocationOSfromReceived.id == self.flt_org_struct_id)
            )

    def _join_hosp_bed(self):
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_HospitalBed = self.model_provider.get('ActionProperty_HospitalBed')

        q_hosp_bed_sq = self.session.query(ActionProperty.id.label('ap_id'))\
            .join(ActionPropertyType)\
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_HOSP_BED_CODE,
                    ActionProperty.action_id == self.MovingAction.id)\
            .limit(1)

        self.query = self.query.outerjoin(
            ActionProperty_HospitalBed, ActionProperty_HospitalBed.id == q_hosp_bed_sq
        ).outerjoin(
            self.MovingOSHB, self.MovingOSHB.id == ActionProperty_HospitalBed.value_
        )

    def _join_leaved(self):
        if self._leaved_joined:
            return

        Action = self.model_provider.get('Action')
        ActionType = self.model_provider.get('ActionType')

        q_leaved = self.session.query(Action.id.label('action_id')).join(
            ActionType
        ).filter(
            Action.event_id == self.BaseEvent.id,
            ActionType.flatCode == STATIONARY_LEAVED_CODE,
            Action.deleted == 0
        ).order_by(
            Action.begDate.desc()
        )
        if self.history:
            # выписка попадает во временной интервал
            q_leaved = q_leaved.filter(
                Action.begDate < self.end_dt,
                or_(Action.endDate.is_(None),
                    Action.endDate >= self.start_dt)
            )
        q_leaved = q_leaved.limit(1)

        self.query = self.query.outerjoin(
            self.LeavedAction, self.LeavedAction.id == q_leaved
        )
        self._leaved_joined = True

    def _join_moving_os_transfer(self):
        if self._moving_os_transfer_joined:
            return

        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_OrgStructure = self.model_provider.get('ActionProperty_OrgStructure')
        AP_OS_Moving_Transfer = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving_Transfer')

        q_os_moving_transfer_sq = self.session.query(ActionProperty.id) \
            .join(ActionPropertyType) \
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                    ActionProperty.action_id == self.MovingAction.id) \
            .limit(1)

        self.query = self.query.outerjoin(
            AP_OS_Moving_Transfer, AP_OS_Moving_Transfer.id == q_os_moving_transfer_sq
        ).outerjoin(
            self.MovingOrgStructTransfer, self.MovingOrgStructTransfer.id == AP_OS_Moving_Transfer.value_
        )
        self._moving_os_transfer_joined = True

    def _join_movings_transfered_through(self):
        if self._moving_transfer_through_joined:
            return

        Action = self.model_provider.get('Action')
        ActionThrough = aliased(Action, name='ActionThrough')
        ActionType = self.model_provider.get('ActionType')
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_OrgStructure = self.model_provider.get('ActionProperty_OrgStructure')

        AP_OS_Moving_Transfer = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving_TransferThr')
        AP_OS_Moving_Stay = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving_StayThr')

        q_os_moving_stay_sq = self.session.query(ActionProperty.id) \
            .join(ActionPropertyType) \
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                    ActionProperty.action_id == ActionThrough.id)
        q_os_moving_stay_sq = q_os_moving_stay_sq.limit(1)

        q_os_moving_transfer_sq = self.session.query(ActionProperty.id) \
            .join(ActionPropertyType) \
            .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                    ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                    ActionProperty.action_id == ActionThrough.id) \
            .limit(1)

        q_movings = self.session.query(ActionThrough).join(
            Event, EventType, rbRequestType, ActionType
        ).join(
            AP_OS_Moving_Stay, AP_OS_Moving_Stay.id == q_os_moving_stay_sq
        ).join(
            # == AP_OS_Moving_Transfer.value_.isnot(None)
            AP_OS_Moving_Transfer, AP_OS_Moving_Transfer.id == q_os_moving_transfer_sq
        ).filter(
            Event.deleted == 0, Event.execDate.is_(None),
            rbRequestType.code.in_(STATIONARY_EVENT_CODES),
            ActionType.flatCode == STATIONARY_MOVING_CODE,
            ActionThrough.begDate < self.end_dt,
            ActionThrough.endDate >= self.start_dt, ActionThrough.endDate < self.end_dt
        ).group_by(
            Event.id
        ).with_entities(
            Event.id.label('event_id'), (func.count(ActionThrough.id) > 0).label('was_transfered_through')
        )
        if self.flt_org_struct_id is not None:
            q_movings = q_movings.filter(
                AP_OS_Moving_Stay.value_ == self.flt_org_struct_id)
        q_movings = q_movings.subquery('TransferedThroughMovingsSQ')

        self.q_movings_transfered_through = q_movings

        self.query = self.query.outerjoin(
            q_movings, q_movings.c.event_id == self.BaseEvent.id
        )
        self._moving_transfer_through_joined = True
