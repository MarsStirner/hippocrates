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
                    'id': hosp.moving_id
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
    def query_hosps_by_latest_location(self, **args):
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
        AP_OS_Moving = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving')
        AP_OS_Received = aliased(ActionProperty_OrgStructure, name='AP_OS_Received')
        MovingOrgStruct = aliased(OrgStructure, name='MovingOrgStruct')
        ReceivedOrgStruct = aliased(OrgStructure, name='ReceivedOrgStruct')

        with_move_date = args.get('with_move_date', False)
        with_org_struct = args.get('with_org_struct', False) or 'org_struct_id' in args
        with_hosp_bed = args.get('with_hosp_bed', False)

        base_query = self.session.query(Event).join(
            Client, EventType, rbRequestType
        ).filter(
            Event.deleted == 0, Event.execDate.is_(None),
            rbRequestType.code.in_(STATIONARY_EVENT_CODES),
        )
#         if 'externalId' in kwargs:
#             base_query = base_query.filter(Event.externalId == kwargs['externalId'])
#         if 'clientId' in kwargs:
#             base_query = base_query.filter(Event.client_id == kwargs['clientId'])
#         if 'execPersonId' in kwargs:
#             base_query = base_query.filter(Event.execPerson_id == kwargs['execPersonId'])

        # самая поздняя дата движения для каждого обращения пациента
        q_action_begdates = self.session.query(Action).join(
            Event, EventType, rbRequestType, ActionType,
        ).filter(
            Event.deleted == 0, Action.deleted == 0, Event.execDate.is_(None),
            rbRequestType.code.in_(STATIONARY_EVENT_CODES),
            ActionType.flatCode == STATIONARY_MOVING_CODE
        ).with_entities(
            func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
        ).group_by(
            Event.id
        ).subquery('MaxActionBegDates')

        # самое позднее движение (включая уже и дату и id, если даты совпадают)
        # для каждого обращения пациента
        q_latest_movings_ids = self.session.query(Action).join(
            q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                    q_action_begdates.c.event_id == Action.event_id)
        ).with_entities(
            func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
        ).group_by(
            Action.event_id
        ).subquery('EventLatestMovings')

        q_latest_movings = self.session.query(MovingAction) \
            .join(q_latest_movings_ids, MovingAction.id == q_latest_movings_ids.c.action_id) \
            .with_entities(
                MovingAction.id.label('action_id'), MovingAction.event_id.label('event_id'),
                MovingAction.begDate.label('begDate'), MovingAction.endDate.label('endDate')) \
            .subquery('q_latest_movings')

        q_received = self.session.query(Action.id.label('action_id')).join(
            ActionType
        ).filter(
            Action.event_id == Event.id,
            ActionType.flatCode == STATIONARY_RECEIVED_CODE,
            Action.deleted == 0
        ).order_by(
            Action.begDate.desc()
        ).limit(1)

        base_query = base_query.outerjoin(
            q_latest_movings, Event.id == q_latest_movings.c.event_id
        ).outerjoin(
            ReceivedAction, ReceivedAction.id == q_received
        ).filter(
            or_(q_latest_movings.c.event_id.isnot(None),
                ReceivedAction.id.isnot(None)),
            func.IF(q_latest_movings.c.event_id.isnot(None),
                    # движение попадает во временной интервал
                    and_(q_latest_movings.c.begDate <= args['end_dt'],
                         or_(q_latest_movings.c.endDate.is_(None),
                             args['start_dt'] <= q_latest_movings.c.endDate)
                         ),
                    # поступление попадает во временной интервал
                    and_(ReceivedAction.begDate <= args['end_dt'],
                         or_(ReceivedAction.endDate.is_(None),
                             args['start_dt'] <= ReceivedAction.endDate)
                         )
                    )
        )
        if with_org_struct:
            q_os_stay_sq = self.session.query(ActionProperty.id) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                        ActionProperty.action_id == q_latest_movings.c.action_id) \
                .limit(1)
            q_os_transfer_sq = self.session.query(ActionProperty.id) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                        ActionProperty.action_id == ReceivedAction.id) \
                .limit(1)
            base_query = base_query.outerjoin(
                AP_OS_Moving, AP_OS_Moving.id == q_os_stay_sq
            ).outerjoin(
                MovingOrgStruct, MovingOrgStruct.id == AP_OS_Moving.value_
            ).outerjoin(
                AP_OS_Received, AP_OS_Received.id == q_os_transfer_sq
            ).outerjoin(
                ReceivedOrgStruct, ReceivedOrgStruct.id == AP_OS_Received.value_
            )

            if 'org_struct_id' in args:
                flt_os = safe_int(args['org_struct_id'])
                base_query = base_query.filter(
                    func.IF(q_latest_movings.c.event_id.isnot(None),
                            MovingOrgStruct.id == flt_os,
                            ReceivedOrgStruct.id == flt_os)
                )
        if with_hosp_bed:
            q_hosp_bed_sq = self.session.query(ActionProperty.id.label('ap_id')) \
                .join(ActionPropertyType) \
                .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                        ActionPropertyType.code == STATIONARY_HOSP_BED_CODE,
                        ActionProperty.action_id == q_latest_movings.c.action_id) \
                .limit(1)
            base_query = base_query.outerjoin(
                ActionProperty_HospitalBed, ActionProperty_HospitalBed.id == q_hosp_bed_sq
            ).outerjoin(
                OrgStructure_HospitalBed,
                OrgStructure_HospitalBed.id == ActionProperty_HospitalBed.value_
            )

        base_query = base_query.with_entities(
            Event,
            q_latest_movings.c.action_id.label('moving_id'),
            ReceivedAction.id.label('received_id')
        )
        if with_move_date:
            base_query = base_query.add_columns(
                func.IF(q_latest_movings.c.event_id.isnot(None),
                        q_latest_movings.c.begDate,
                        ReceivedAction.begDate).label('move_date')
            )
        if with_org_struct:
            base_query = base_query.add_columns(
                func.IF(q_latest_movings.c.event_id.isnot(None),
                        MovingOrgStruct.name,
                        ReceivedOrgStruct.name).label('os_name')
            )
        if with_hosp_bed:
            base_query = base_query.add_columns(
                OrgStructure_HospitalBed.name.label('hosp_bed_name')
            )
        if args.get('order_by_move_date', False):
            base_query = base_query.order_by(
                func.IF(q_latest_movings.c.event_id.isnot(None),
                        q_latest_movings.c.begDate,
                        ReceivedAction.begDate).desc()
            )

        return base_query

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
            AP_OS_Moving = aliased(ActionProperty_OrgStructure, name='AP_OS_Moving')
            AP_OS_Received = aliased(ActionProperty_OrgStructure, name='AP_OS_Received')
            MovingOrgStruct = aliased(OrgStructure, name='MovingOrgStruct')
            ReceivedOrgStruct = aliased(OrgStructure, name='ReceivedOrgStruct')

            with_move_date = args.get('with_move_date', False)
            with_org_struct = args.get('with_org_struct', False) or 'org_struct_id' in args
            with_hosp_bed = args.get('with_hosp_bed', False)

            base_query = self.session.query(Event).join(
                Client, EventType, rbRequestType
            ).filter(
                Event.deleted == 0, Event.execDate.is_(None),
                rbRequestType.code.in_(STATIONARY_EVENT_CODES),
            )
            #         if 'externalId' in kwargs:
            #             base_query = base_query.filter(Event.externalId == kwargs['externalId'])
            #         if 'clientId' in kwargs:
            #             base_query = base_query.filter(Event.client_id == kwargs['clientId'])
            #         if 'execPersonId' in kwargs:
            #             base_query = base_query.filter(Event.execPerson_id == kwargs['execPersonId'])

            # самая поздняя дата движения для каждого обращения пациента
            q_action_begdates = self.session.query(Action).join(
                Event, EventType, rbRequestType, ActionType,
            ).filter(
                Event.deleted == 0, Action.deleted == 0, Event.execDate.is_(None),
                rbRequestType.code.in_(STATIONARY_EVENT_CODES),
                ActionType.flatCode == STATIONARY_MOVING_CODE
            ).with_entities(
                func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
            ).group_by(
                Event.id
            ).subquery('MaxActionBegDates')

            # самое позднее движение (включая уже и дату и id, если даты совпадают)
            # для каждого обращения пациента
            q_latest_movings_ids = self.session.query(Action).join(
                q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                        q_action_begdates.c.event_id == Action.event_id)
            ).with_entities(
                func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
            ).group_by(
                Action.event_id
            ).subquery('EventLatestMovings')

            q_latest_movings = self.session.query(MovingAction) \
                .join(q_latest_movings_ids, MovingAction.id == q_latest_movings_ids.c.action_id) \
                .with_entities(
                MovingAction.id.label('action_id'), MovingAction.event_id.label('event_id'),
                MovingAction.begDate.label('begDate'), MovingAction.endDate.label('endDate')) \
                .subquery('q_latest_movings')

            q_received = self.session.query(Action.id.label('action_id')).join(
                ActionType
            ).filter(
                Action.event_id == Event.id,
                ActionType.flatCode == STATIONARY_RECEIVED_CODE,
                Action.deleted == 0
            ).order_by(
                Action.begDate.desc()
            ).limit(1)

            base_query = base_query.outerjoin(
                q_latest_movings, Event.id == q_latest_movings.c.event_id
            ).outerjoin(
                ReceivedAction, ReceivedAction.id == q_received
            ).filter(
                or_(q_latest_movings.c.event_id.isnot(None),
                    ReceivedAction.id.isnot(None)),
                func.IF(q_latest_movings.c.event_id.isnot(None),
                        # движение попадает во временной интервал
                        and_(q_latest_movings.c.begDate <= args['end_dt'],
                             or_(q_latest_movings.c.endDate.is_(None),
                                 args['start_dt'] <= q_latest_movings.c.endDate)
                             ),
                        # поступление попадает во временной интервал
                        and_(ReceivedAction.begDate <= args['end_dt'],
                             or_(ReceivedAction.endDate.is_(None),
                                 args['start_dt'] <= ReceivedAction.endDate)
                             )
                        )
            )
            if with_org_struct:
                q_os_stay_sq = self.session.query(ActionProperty.id) \
                    .join(ActionPropertyType) \
                    .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                            ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE,
                            ActionProperty.action_id == q_latest_movings.c.action_id) \
                    .limit(1)
                q_os_transfer_sq = self.session.query(ActionProperty.id) \
                    .join(ActionPropertyType) \
                    .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                            ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
                            ActionProperty.action_id == ReceivedAction.id) \
                    .limit(1)
                base_query = base_query.outerjoin(
                    AP_OS_Moving, AP_OS_Moving.id == q_os_stay_sq
                ).outerjoin(
                    MovingOrgStruct, MovingOrgStruct.id == AP_OS_Moving.value_
                ).outerjoin(
                    AP_OS_Received, AP_OS_Received.id == q_os_transfer_sq
                ).outerjoin(
                    ReceivedOrgStruct, ReceivedOrgStruct.id == AP_OS_Received.value_
                )

                if 'org_struct_id' in args:
                    flt_os = safe_int(args['org_struct_id'])
                    base_query = base_query.filter(
                        func.IF(q_latest_movings.c.event_id.isnot(None),
                                MovingOrgStruct.id == flt_os,
                                ReceivedOrgStruct.id == flt_os)
                    )
            if with_hosp_bed:
                q_hosp_bed_sq = self.session.query(ActionProperty.id.label('ap_id')) \
                    .join(ActionPropertyType) \
                    .filter(ActionProperty.deleted == 0, ActionPropertyType.deleted == 0,
                            ActionPropertyType.code == STATIONARY_HOSP_BED_CODE,
                            ActionProperty.action_id == q_latest_movings.c.action_id) \
                    .limit(1)
                base_query = base_query.outerjoin(
                    ActionProperty_HospitalBed, ActionProperty_HospitalBed.id == q_hosp_bed_sq
                ).outerjoin(
                    OrgStructure_HospitalBed,
                    OrgStructure_HospitalBed.id == ActionProperty_HospitalBed.value_
                )

            base_query = base_query.with_entities(
                Event,
                q_latest_movings.c.action_id.label('moving_id'),
                ReceivedAction.id.label('received_id')
            )
            if with_move_date:
                base_query = base_query.add_columns(
                    func.IF(q_latest_movings.c.event_id.isnot(None),
                            q_latest_movings.c.begDate,
                            ReceivedAction.begDate).label('move_date')
                )
            if with_org_struct:
                base_query = base_query.add_columns(
                    func.IF(q_latest_movings.c.event_id.isnot(None),
                            MovingOrgStruct.name,
                            ReceivedOrgStruct.name).label('os_name')
                )
            if with_hosp_bed:
                base_query = base_query.add_columns(
                    OrgStructure_HospitalBed.name.label('hosp_bed_name')
                )
            if args.get('order_by_move_date', False):
                base_query = base_query.order_by(
                    func.IF(q_latest_movings.c.event_id.isnot(None),
                            q_latest_movings.c.begDate,
                            ReceivedAction.begDate).desc()
                )

            return base_query

    def get_latest_hosps(self, **kwargs):
        Event = self.model_provider.get('Event')

        for_date = safe_datetime(kwargs.get('for_date')) or datetime.datetime.now()
        start_dt = for_date.replace(hour=8, minute=0, second=0, microsecond=0)
        end_dt = start_dt + datetime.timedelta(days=1)
        end_dt = end_dt.replace(hour=7, minute=59, second=59, microsecond=0)

        args = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'with_move_date': True,
            'with_org_struct': True,
            'with_hosp_bed': True,
            'order_by_move_date': True
        }
        if 'org_struct_id' in kwargs:
            args['org_struct_id'] = safe_int(kwargs['org_struct_id'])
        query = self.query_hosps_by_latest_location(**args)

        self.query = query.options(
            contains_eager(Event.client),
            joinedload(Event.execPerson)
        )
        return self.get_paginated(kwargs)

