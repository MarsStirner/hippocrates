# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import aliased, contains_eager, joinedload

from nemesis.lib.utils import safe_datetime, safe_int
from nemesis.lib.const import STATIONARY_EVENT_CODES, STATIONARY_MOVING_CODE, \
    STATIONARY_RECEIVED_CODE, STATIONARY_ORG_STRUCT_STAY_CODE, \
    STATIONARY_ORG_STRUCT_TRANSFER_CODE, STATIONARY_HOSP_BED_CODE
from nemesis.lib.data_ctrl.base import BaseSelecter, BaseModelController


class HospitalizationController(BaseModelController):

    def get_current_hosps(self, **args):
        sel = HospitalizationSelector()
        hosps_data = sel.get_latest_hosps(**args)
        hosp_list = []
        for hosp in hosps_data.items:
            h = {
                'id': hosp.Event.id,
                'external_id': hosp.Event.externalId,
                'exec_person': {
                    'id': hosp.Event.execPerson_id,
                    'short_name': hosp.Event.execPerson.shortNameText
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
                'hosp_bed_name': hosp.hosp_bed_name
            }
            hosp_list.append(h)
        return {
            'items': hosp_list,
            'count': hosps_data.total,
            'total_pages': hosps_data.pages
        }


class HospitalizationSelector(BaseSelecter):

    def __init__(self, query=None):
        Action = self.model_provider.get('Action')
        OrgStructure = self.model_provider.get('OrgStructure')
        OrgStructure_HospitalBed = self.model_provider.get('OrgStructure_HospitalBed')

        self.BaseEvent = self.model_provider.get('Event')
        self.MovingAction = aliased(Action, name='LatestMovingAction')
        self.ReceivedAction = aliased(Action, name='ReceivedAction')
        self.LocationOSfromMoving = aliased(OrgStructure, name='LocationOrgStructFromMoving')
        self.LocationOSfromReceived = aliased(OrgStructure, name='LocationOrgStructFromReceived')
        self.MovingOSHB = aliased(OrgStructure_HospitalBed, name='MovingHospitalBed')

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

    def _query_hosps_by_latest_location(self, flt_start_dt, flt_end_dt, history=False):
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
        ).limit(1)
        if history:
            # движение попадает во временной интервал
            q_latest_moving = q_latest_moving.filter(
                Action.begDate <= flt_end_dt,
                or_(Action.endDate.is_(None),
                    Action.endDate >= flt_start_dt)
            )

        q_received = self.session.query(Action.id.label('action_id')).join(
            ActionType
        ).filter(
            Action.event_id == self.BaseEvent.id,
            ActionType.flatCode == STATIONARY_RECEIVED_CODE,
            Action.deleted == 0
        ).order_by(
            Action.begDate.desc()
        ).limit(1)
        if history:
            # поступление попадает во временной интервал
            q_latest_moving = q_latest_moving.filter(
                Action.begDate <= flt_end_dt,
                or_(Action.endDate.is_(None),
                    Action.endDate >= flt_start_dt)
            )

        self.query = self.query.outerjoin(
            self.MovingAction, self.MovingAction.id == q_latest_moving
        ).outerjoin(
            self.ReceivedAction, self.ReceivedAction.id == q_received
        ).filter(
            or_(self.MovingAction.id.isnot(None),
                self.ReceivedAction.id.isnot(None)),
        )
        if not history:
            self.query = self.query.filter(
                func.IF(self.MovingAction.id.isnot(None),
                        # движение попадает во временной интервал
                        and_(self.MovingAction.begDate <= flt_end_dt,
                             or_(self.MovingAction.endDate.is_(None),
                                 flt_start_dt <= self.MovingAction.endDate)
                             ),
                        # поступление попадает во временной интервал
                        and_(self.ReceivedAction.begDate <= flt_end_dt,
                             or_(self.ReceivedAction.endDate.is_(None),
                                 flt_start_dt <= self.ReceivedAction.endDate)
                             )
                        )
            )

    def _join_location_org_structure(self, org_struct_id=None):
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

        if org_struct_id is not None:
            self.query = self.query.filter(
                func.IF(self.MovingAction.id.isnot(None),
                        self.LocationOSfromMoving.id == org_struct_id,
                        self.LocationOSfromReceived.id == org_struct_id)
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

    def query_hosps_filter(self, **args):
        Event = self.model_provider.get('Event')
        Action = self.model_provider.get('Action')
        EventType = self.model_provider.get('EventType')
        rbRequestType = self.model_provider.get('rbRequestType')
        ActionType = self.model_provider.get('ActionType')
        Client = self.model_provider.get('Client')
        ActionProperty = self.model_provider.get('ActionProperty')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        ActionProperty_OrgStructure = self.model_provider.get('ActionProperty_OrgStructure')
        ActionProperty_HospitalBed = self.model_provider.get('ActionProperty_HospitalBed')
        OrgStructure_HospitalBed = self.model_provider.get('OrgStructure_HospitalBed')
        OrgStructure = self.model_provider.get('OrgStructure')

        MovingAction = aliased(Action, name='MovingAction')
        ReceivedAction = aliased(Action, name='ReceivedAction')
        LeavedAction = aliased(Action, name='LeavedAction')
        AP_OS_Moving_Stay = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving_Stay')
        AP_OS_Moving_Transfer = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving_Transfer')
        AP_OS_Received_Transfer = aliased(ActionProperty_OrgStructure, name='AP_OS_Received_Transfer')
        MovingOrgStructStay = aliased(OrgStructure, name='MovingOrgStructStay')
        MovingOrgStructTransfer = aliased(OrgStructure, name='MovingOrgStructTransfer')
        ReceivedOrgStructTransfer = aliased(OrgStructure, name='ReceivedOrgStructTransfer')

        with_move_date = args.get('with_move_date', False)
        with_moving_end_date = args.get('with_moving_end_date', False)
        with_org_struct = args.get('with_org_struct', False) or 'org_struct_id' in args
        with_hosp_bed = args.get('with_hosp_bed', False)

        patients_state = args.get('patients_state', False)

        beg_date = args.get('start_dt')
        end_date = args.get('end_dt')

        if with_org_struct:
            q_os_moving_stay_sq = self.session.query(ActionProperty.id) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                        ActionProperty.action_id == MovingAction.id) \
                .limit(1)
            q_os_moving_transfer_sq = self.session.query(ActionProperty.id) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                        ActionProperty.action_id == MovingAction.id) \
                .limit(1)
            q_os_received_transfer_sq = self.session.query(ActionProperty.id) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                        ActionProperty.action_id == ReceivedAction.id) \
                .limit(1)

            base_query = base_query.outerjoin(
                AP_OS_Moving_Stay, AP_OS_Moving_Stay.id == q_os_moving_stay_sq
            ).outerjoin(
                MovingOrgStructStay, MovingOrgStructStay.id == AP_OS_Moving_Stay.value_
            ).outerjoin(
                AP_OS_Moving_Transfer, AP_OS_Moving_Transfer.id == q_os_moving_transfer_sq
            ).outerjoin(
                MovingOrgStructTransfer, MovingOrgStructTransfer.id == AP_OS_Moving_Transfer.value_
            ).outerjoin(
                AP_OS_Received_Transfer, AP_OS_Received_Transfer.id == q_os_received_transfer_sq
            ).outerjoin(
                ReceivedOrgStructTransfer, ReceivedOrgStructTransfer.id == AP_OS_Received_Transfer.value_
            )

            if 'org_struct_id' in args:
                flt_os = safe_int(args['org_struct_id'])
                base_query = base_query.filter(
                    func.IF(MovingAction.id.isnot(None),
                            MovingOrgStructStay.id == flt_os,
                            ReceivedOrgStructTransfer.id == flt_os)
                )

        if with_hosp_bed:
            q_hosp_bed_sq = self.session.query(ActionProperty.id.label('ap_id'))\
                .join(ActionPropertyType)\
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_HOSP_BED_CODE,
                        ActionProperty.action_id == MovingAction.id)\
                .limit(1)
            base_query = base_query.outerjoin(
                ActionProperty_HospitalBed, ActionProperty_HospitalBed.id == q_hosp_bed_sq
            ).outerjoin(
                OrgStructure_HospitalBed,
                OrgStructure_HospitalBed.id == ActionProperty_HospitalBed.value_
            )

        base_query = base_query.with_entities(
            Event,
            MovingAction.id.label('moving_id'),
            ReceivedAction.id.label('received_id')
        )
        if with_move_date:
            base_query = base_query.add_columns(
                func.IF(MovingAction.id.isnot(None),
                        MovingAction.begDate,
                        ReceivedAction.begDate).label('move_date')
            )
        if with_moving_end_date:
            base_query = base_query.add_columns(
                MovingAction.endDate.label('moving_end_date')
            )
        if with_org_struct:
            base_query = base_query.add_columns(
                func.IF(MovingAction.id.isnot(None),
                        MovingOrgStructStay.name,
                        ReceivedOrgStructTransfer.name).label('os_name')
            )
        if with_hosp_bed:
            base_query = base_query.add_columns(
                OrgStructure_HospitalBed.name.label('hosp_bed_name')
            )
        if args.get('order_by_move_date', False):
            base_query = base_query.order_by(
                func.IF(MovingAction.id.isnot(None),
                        MovingAction.begDate,
                        ReceivedAction.begDate).desc()
            )

        # Текущие - Action.endDate для движения пусто или больше end_date,
        # отделение пребывания равно текущему отделению пользователя. Плюс отображаем пациентов, у которых есть
        # поступление в это отделение, но их еще не разместили на койке (в таком случае, у этих пациентов в столбце
        # "Койка" будет отображаться гиперссылка "Положить на койку").
        if patients_state == 'current':
            base_query = base_query.filter(
                func.IF(MovingAction.id.isnot(None),
                        or_(MovingAction.endDate.is_(None),
                            MovingAction.endDate >= end_date),
                        or_(ReceivedAction.endDate.is_(None),
                            ReceivedAction.endDate >= end_date)
                        )
            )
        # Поступившие - Action.begDate для движения более или равно beg_date, а endDate любая, отделение
        # пребывания равно текущему отделению пользователя;
        elif patients_state == 'received':
            base_query = base_query.filter(
                func.IF(MovingAction.id.isnot(None),
                        and_(MovingAction.begDate >= beg_date,
                             MovingAction.begDate <= end_date),
                        and_(ReceivedAction.begDate >= beg_date,
                             ReceivedAction.begDate <= end_date),
                        )
            )
        # Переведенные - Action.endDate между beg_date и end_date, а поле "Переведен в отделение"
        # не пустое, отделение пребывания равно текущему отделению пользователя;
        # todo: невозможно получить переведенных пациентов при данном подходе, так как у последнего движения поле
        # todo: "Переведен в отделение" будет всегда пустым
        elif patients_state == 'transferred':
            base_query = base_query.filter(
                MovingAction.endDate >= beg_date,
                MovingAction.endDate <= end_date,
                MovingOrgStructTransfer.id.isnot(None)
            )
        # Выписанные - Action.endDate между beg_date и end_date, а поле "Переведен в отделение" пусто. Присутствует
        # "Выписной эпикриз" - но необязательно для того, чтобы считать пациента убывшим из отделения.
        elif patients_state == 'leaved':
            q_leaved = self.session.query(Action.id.label('action_id')).join(
                ActionType
            ).filter(
                Action.event_id == Event.id,
                ActionType.flatCode == STATIONARY_LEAVED_CODE,
                Action.deleted == 0
            ).order_by(
                Action.begDate.desc()
            ).limit(1)

            base_query = base_query.join(
                LeavedAction, LeavedAction.id == q_leaved
            ).filter(
                func.IF(MovingAction.id.isnot(None),
                        and_(MovingAction.endDate >= beg_date,
                             MovingAction.endDate <= end_date),
                        and_(ReceivedAction.endDate >= beg_date,
                             ReceivedAction.endDate <= end_date),
                        )
            )

        return base_query

    def get_latest_hosps(self, **kwargs):
        for_date = safe_datetime(kwargs.get('for_date')) or datetime.datetime.now()
        start_dt = for_date.replace(hour=8, minute=0, second=0, microsecond=0)
        end_dt = start_dt + datetime.timedelta(days=1)
        end_dt = end_dt.replace(hour=7, minute=59, second=59, microsecond=0)

        flt_org_struct_id = safe_int(kwargs.get('org_struct_id'))

        self._query_hosps_by_latest_location(start_dt, end_dt)
        self._join_location_org_structure(flt_org_struct_id)
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

    def get_latest_hosps1(self, **kwargs):
        Event = self.model_provider.get('Event')

        for_date = safe_datetime(kwargs.get('for_date')) or datetime.datetime.now()
        start_dt = for_date or for_date.replace(hour=8, minute=0, second=0, microsecond=0)
        end_dt = safe_datetime(kwargs.get('end_dt'))
        if not end_dt:
            end_dt = start_dt + datetime.timedelta(days=1)
            end_dt = end_dt.replace(hour=7, minute=59, second=59, microsecond=0)

        args = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'with_move_date': True,
            'with_moving_end_date': True,
            'with_org_struct': True,
            'with_hosp_bed': True,
            'order_by_move_date': True
        }
        if 'org_struct_id' in kwargs:
            args['org_struct_id'] = safe_int(kwargs['org_struct_id'])
        if 'patients_state' in kwargs:
            args['patients_state'] = kwargs['patients_state']

        if 'filter' in kwargs:
            query = self.query_hosps_filter(**args)
        else:
            query = self.query_hosps_by_latest_location(**args)

        self.query = query.options(
            contains_eager(Event.client),
            joinedload(Event.execPerson)
        )
        return self.get_paginated(kwargs)
