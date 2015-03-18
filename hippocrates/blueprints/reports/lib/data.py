# -*- coding: utf-8 -*-
import os
import exceptions
from datetime import date, timedelta, datetime

from ..app import module, _config
from flask.ext.sqlalchemy import SQLAlchemy
from ..utils import get_lpu_session


class Statistics(object):

    def __init__(self):
        self.db_session = get_lpu_session()
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)

    def __del__(self):
        self.db_session.close()

    def get_patients(self):
        query = '''
                    SELECT count(`Action`.`id`) as number
                           FROM `Action`
                           INNER JOIN Event
                           ON Event.id = Action.event_id
                           WHERE `Action`.`deleted` = 0 AND `Action`.`actionType_id` = 113
                           and Event.deleted = 0 and `Action`.endDate is NULL;
        '''
        return self.db_session.execute(query).first()

    def get_patients_orgStruct(self):
        query = '''
                    SELECT count(`Action`.`id`) as number, OrgStructure.id, OrgStructure.name
                    FROM `Action`
                    INNER JOIN Event
                    ON Event.id = Action.event_id
                    INNER JOIN `ActionProperty`
                    ON `Action`.`id` = `ActionProperty`.`action_id`
                    INNER  JOIN `ActionProperty_OrgStructure`
                    ON ActionProperty.id = `ActionProperty_OrgStructure`.`id` AND `ActionProperty`.`type_id` = 7021
                    INNER JOIN OrgStructure
                    ON ActionProperty_OrgStructure.value = OrgStructure.id
                    WHERE `Action`.`deleted` = 0 AND `Action`.`actionType_id` = 113
                    and Event.deleted = 0 and `Action`.endDate is NULL
                    group by OrgStructure.id
                    ORDER BY OrgStructure.name;
        '''
        return self.db_session.execute(query)

    def get_postup(self):
        query = u'''
                    SELECT
                        count(Action.id) as number
                    FROM
                        Action
                            INNER JOIN
                        ActionType ON Action.`actionType_id` = ActionType.`id`
                            INNER JOIN
                        ActionProperty ON Action.`id` = ActionProperty.`action_id`
                            INNER JOIN
                        ActionProperty_HospitalBed ON ActionProperty.`id` = ActionProperty_HospitalBed.`id`
                            INNER JOIN
                        Event ON Action.`event_id` = Event.`id`
                            INNER JOIN
                        (SELECT
                            Action.id, ActionProperty_HospitalBedProfile.value
                        FROM
                            Action
                        INNER JOIN ActionType ON Action.`actionType_id` = ActionType.`id`
                        INNER JOIN ActionProperty ON Action.`id` = ActionProperty.`action_id`
                        INNER JOIN ActionPropertyType ON ActionPropertyType.`id` = ActionProperty.`type_id`
                        INNER JOIN ActionProperty_HospitalBedProfile ON ActionProperty.`id` = ActionProperty_HospitalBedProfile.`id`
                        INNER JOIN rbHospitalBedProfile ON ActionProperty_HospitalBedProfile.`value` = rbHospitalBedProfile.`id`
                        WHERE
                            (ActionType.`flatCode` = 'moving')
                                AND (ActionPropertyType.`code` = 'hospitalBedProfile')
                                AND ((Action.`begDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                                AND (Action.`begDate` <= '{1} 08:00:00'))) sz ON Action.id = sz.id
                    WHERE
                        ((Action.`begDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                            AND (Action.`begDate` <= '{1} 08:00:00'))
                            AND (ActionType.`flatCode` = 'moving')
                            AND (Action.`deleted` = 0)
                            AND (Event.`deleted` = 0)
                            AND (ActionProperty.`deleted` = 0)
                            AND (Action.id IN (SELECT
                                id
                            FROM
                                (SELECT
                                    Action.id, min(Action.id)
                                FROM
                                    Action
                                JOIN ActionType ON Action.actionType_id = ActionType.id
                                WHERE
                                    ActionType.flatCode = 'moving'
                                        AND Action.begDate IS NOT NULL
                                        AND Action.deleted = 0
                                GROUP BY event_id) A))
                    '''.format(self.yesterday.strftime('%Y-%m-%d'), self.today.strftime('%Y-%m-%d'))
        return self.db_session.execute(query).first()

    def get_vypis(self):
        query = u'''
                    SELECT
                        count(Action.id) as number
                    FROM
                        Action
                            INNER JOIN
                        ActionType ON Action.`actionType_id` = ActionType.`id`
                            INNER JOIN
                        ActionProperty ON Action.`id` = ActionProperty.`action_id`
                            INNER JOIN
                        ActionProperty_HospitalBed ON ActionProperty.`id` = ActionProperty_HospitalBed.`id`
                            INNER JOIN
                        OrgStructure_HospitalBed ON ActionProperty_HospitalBed.`value` = OrgStructure_HospitalBed.`id`
                            INNER JOIN
                        Event ON Action.`event_id` = Event.`id`
                            INNER JOIN
                        (SELECT
                            Action.id, ActionProperty_HospitalBedProfile.value
                        FROM
                            Action
                        INNER JOIN ActionType ON Action.`actionType_id` = ActionType.`id`
                        INNER JOIN ActionProperty ON Action.`id` = ActionProperty.`action_id`
                        INNER JOIN ActionPropertyType ON ActionPropertyType.`id` = ActionProperty.`type_id`
                        INNER JOIN ActionProperty_HospitalBedProfile ON ActionProperty.`id` = ActionProperty_HospitalBedProfile.`id`
                        INNER JOIN rbHospitalBedProfile ON ActionProperty_HospitalBedProfile.`value` = rbHospitalBedProfile.`id`
                        WHERE
                            (ActionType.`flatCode` = 'moving')
                                AND (ActionPropertyType.`code` = 'hospitalBedProfile')
                                AND ((Action.`endDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                                AND (Action.`endDate` <= '{1} 08:00:00'))) sz ON Action.id = sz.id
                    WHERE
                        ((Action.`endDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                            AND (Action.`endDate` <= '{1} 08:00:00'))
                            AND (ActionType.`flatCode` = 'moving')
                            AND (Action.`deleted` = 0)
                            AND (Event.`deleted` = 0)
                            AND (ActionProperty.`deleted` = 0)
                            AND (Action.id IN (SELECT
                                id
                            FROM
                                (SELECT
                                    max(Action.id) id
                                FROM
                                    Action
                                JOIN ActionType ON Action.actionType_id = ActionType.id
                                WHERE
                                    ActionType.flatCode = 'moving'
                                        AND Action.begDate IS NOT NULL
                                        AND Action.deleted = 0
                                GROUP BY event_id) A))
                            AND Action.event_id NOT IN (SELECT
                                e.id
                            FROM
                                Event e
                                    INNER JOIN
                                rbResult ON rbResult.id = e.result_id
                                    AND rbResult.name = 'умер');
                    '''.format(self.yesterday.strftime('%Y-%m-%d'), self.today.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def get_hospitalization_figures(self):
        query = u'''
                    SELECT
                        count(Event.id) AS total,
                        f.totalondate,
                        postupondatebefore1.postupondatebefore1,
                        postupbefore1.postupbefore1,
                        postupondateafter15.postupondateafter15,
                        postupafter15.postupafter15,
                        postupondateafter18.postupondateafter18,
                        postupafter18.postupafter18,
                        orit.orit AS orittotal,
                        oritondate.oritondate,
                        pervtotalondate.pervtotalondate,
                        pervtotal.pervtotal,
                        povttotalondate.povttotalondate,
                        povttotal.povttotal,
                        reopenondate.reopenondate,
                        reopentotal.reopentotal,
                        gospondate.gospondate,
                        gosptotal.gosptotal
                    FROM
                        Event
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS totalondate, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS f ON EventType.purpose_id = f.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupondatebefore1,
                                EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')
                                AND ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) < '1') AS postupondatebefore1 ON EventType.purpose_id = postupondatebefore1.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupbefore1, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) < '1') AS postupbefore1 ON EventType.purpose_id = postupbefore1.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupondateafter15,
                                EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')
                                AND ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) >= '15') AS postupondateafter15 ON EventType.purpose_id = postupondateafter15.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupafter15, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) >= '15') AS postupafter15 ON EventType.purpose_id = postupafter15.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupondateafter18,
                                EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')
                                AND ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) >= '18') AS postupondateafter18 ON EventType.purpose_id = postupondateafter18.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS postupafter18, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Client ON Event.client_id = Client.id
                        WHERE
                            ((year(Event.setDate) - year(Client.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(Client.birthDate, '%m%d'))) >= '18') AS postupafter18 ON EventType.purpose_id = postupafter18.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'orit', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_OrgStructure ON ActionProperty.id = ActionProperty_OrgStructure.id
                            AND ActionProperty.type_id = 1608
                            AND ActionProperty_OrgStructure.value = 27) AS orit ON EventType.purpose_id = orit.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'oritondate', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_OrgStructure ON ActionProperty.id = ActionProperty_OrgStructure.id
                            AND ActionProperty.type_id = 1608
                            AND ActionProperty_OrgStructure.value = 27
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS oritondate ON EventType.purpose_id = oritondate.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS pervtotalondate,
                                EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                            AND Event.isPrimary = 1
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS pervtotalondate ON EventType.purpose_id = pervtotalondate.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS pervtotal, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                            AND Event.isPrimary = 1) AS pervtotal ON EventType.purpose_id = pervtotal.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS povttotalondate,
                                EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                            AND Event.isPrimary = 2
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS povttotalondate ON EventType.purpose_id = povttotalondate.p
                            LEFT JOIN
                        (SELECT
                            count(Event.id) AS povttotal, EventType.purpose_id AS p
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                            AND Event.isPrimary = 2) AS povttotal ON EventType.purpose_id = povttotal.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'reopenondate', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id
                            AND ActionProperty.type_id = 3910954
                            AND ActionProperty_String.value = 'Да'
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS reopenondate ON EventType.purpose_id = reopenondate.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'reopentotal', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id
                            AND ActionProperty.type_id = 3910954
                            AND ActionProperty_String.value = 'Да') AS reopentotal ON EventType.purpose_id = reopentotal.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'gospondate', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id
                            AND ActionProperty.type_id = 1611
                            AND ActionProperty_String.value <> ''
                        WHERE
                            Event.setDate >= CONCAT('{0}', ' 00:00:00')
                                AND Event.setDate <= CONCAT('{0}', ' 23:59:59')) AS gospondate ON EventType.purpose_id = gospondate.p
                            LEFT JOIN
                        (SELECT
                            count(*) AS 'gosptotal', EventType.purpose_id AS 'p'
                        FROM
                            Event
                        INNER JOIN EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            AND Event.deleted = 0
                            AND Event.client_id NOT IN (18)
                        INNER JOIN Action ON Event.id = Action.event_id
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.actionType_id = 112
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id
                            AND ActionProperty.type_id = 1611
                            AND ActionProperty_String.value <> '') AS gosptotal ON EventType.purpose_id = gosptotal.p;
                    '''.format(self.yesterday.strftime('%Y-%m-%d'), self.today.strftime('%Y-%m-%d'))
        return self.db_session.execute(query).first()

    def get_hospitalizations_by_fs(self):
        query = u'''
                    SELECT
                        rbFinance.name, COUNT(rbFinance.name) as number
                    FROM
                        Action
                            INNER JOIN
                        ActionType ON Action.`actionType_id` = ActionType.`id`
                            INNER JOIN
                        ActionProperty ON Action.`id` = ActionProperty.`action_id`
                            INNER JOIN
                        ActionProperty_HospitalBed ON ActionProperty.`id` = ActionProperty_HospitalBed.`id`
                            INNER JOIN
                        Event ON Action.`event_id` = Event.`id`
                            INNER JOIN
                        EventType ON Event.EventType_id = EventType.id
                            INNER JOIN
                        rbFinance ON EventType.finance_id = rbFinance.id
                            INNER JOIN
                        (SELECT
                            Action.id, ActionProperty_HospitalBedProfile.value
                        FROM
                            Action
                        INNER JOIN ActionType ON Action.`actionType_id` = ActionType.`id`
                        INNER JOIN ActionProperty ON Action.`id` = ActionProperty.`action_id`
                        INNER JOIN ActionPropertyType ON ActionPropertyType.`id` = ActionProperty.`type_id`
                        INNER JOIN ActionProperty_HospitalBedProfile ON ActionProperty.`id` = ActionProperty_HospitalBedProfile.`id`
                        INNER JOIN rbHospitalBedProfile ON ActionProperty_HospitalBedProfile.`value` = rbHospitalBedProfile.`id`
                        WHERE
                            (ActionType.`flatCode` = 'moving')
                                AND (ActionPropertyType.`code` = 'hospitalBedProfile')
                                AND ((Action.`begDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                                AND (Action.`begDate` <= '{1} 08:00:00'))) sz ON Action.id = sz.id
                    WHERE
                        ((Action.`begDate` >= '{1} 08:00:00' - INTERVAL 1 DAY)
                            AND (Action.`begDate` <= '{1} 08:00:00'))
                            AND (ActionType.`flatCode` = 'moving')
                            AND (Action.`deleted` = 0)
                            AND (Event.`deleted` = 0)
                            AND (ActionProperty.`deleted` = 0)
                            AND (Action.id IN (SELECT
                                id
                            FROM
                                (SELECT
                                    Action.id, min(Action.id)
                                FROM
                                    Action
                                JOIN ActionType ON Action.actionType_id = ActionType.id
                                WHERE
                                    ActionType.flatCode = 'moving'
                                        AND Action.begDate IS NOT NULL
                                        AND Action.deleted = 0
                                GROUP BY event_id) A))
                    GROUP BY rbFinance.name;
                    '''.format(self.yesterday.strftime('%Y-%m-%d'), self.today.strftime('%Y-%m-%d'))

        return self.db_session.execute(query)


class Patients_Process(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_priemn_postup(self, start, end):
        query = '''SELECT
                      `Action`.`begDate` AS `Datapost`,
                      Client.lastName,
                      Client.firstName,
                      Client.patrName,
                      Event.externalId,
                      OrgStructure.Address
                    FROM `Action`
                     INNER JOIN `ActionProperty`
                        ON `Action`.`id` = `ActionProperty`.`action_id` AND `ActionProperty`.`type_id` = 1608
                    INNER  JOIN `ActionProperty_OrgStructure`
                        ON ActionProperty.id = `ActionProperty_OrgStructure`.`id`
                     INNER JOIN OrgStructure
                        ON ActionProperty_OrgStructure.value = OrgStructure.id
                      INNER JOIN Event
                      ON Event.id = Action.event_id
                      INNER JOIN Client
                      ON Client.id = Event.client_id
                    WHERE `Action`.`deleted` = 0 AND `Action`.`actionType_id` = 112
                    AND (Action.endDate BETWEEN '{0} 08:00:00' AND '{1} 07:59:59')
                    '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query)

    def get_priemn_vypis(self, start, end):
        query = '''SELECT
                      `Action`.`begDate` AS `Datapost`,
                      Client.lastName,
                      Client.firstName,
                      Client.patrName,
                      Event.externalId,
                      OrgStructure.Address
                    FROM `Action`
                     INNER JOIN `ActionProperty`
                        ON `Action`.`id` = `ActionProperty`.`action_id` AND `Action`.`actionType_id` = 113
                    INNER  JOIN `ActionProperty_OrgStructure`
                        ON ActionProperty.id = `ActionProperty_OrgStructure`.`id` AND `ActionProperty`.`type_id` = 7021
                     INNER JOIN OrgStructure
                        ON ActionProperty_OrgStructure.value = OrgStructure.id
                      INNER JOIN VYPISKI
                      ON VYPISKI.Event_id = `Action`.event_id
                      INNER JOIN Event
                      ON Event.id = Action.event_id
                      INNER JOIN Client
                      ON Client.id = Event.client_id
                    WHERE `Action`.`deleted` = 0 AND Event.deleted=0 AND date(`Action`.endDate)=DATE(VYPISKI.`Data vypiski`)
                    AND (VYPISKI.`Data vypiski` BETWEEN '{0} 08:00:00' AND '{1} 07:59:59')
                    '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query)

    def get_priemn_perevod(self, start, end):
        query = '''
                    SELECT
                        `Action`.`begDate` AS `Datapost`,
                        Client.lastName,
                        Client.firstName,
                        Client.patrName,
                        Event.externalId,
                        OrgStructure.Address,
                        Pac_prb.prb AS prb
                    FROM
                        `Action`
                            INNER JOIN
                        `ActionProperty` ON `Action`.`id` = `ActionProperty`.`action_id`
                            AND `Action`.`actionType_id` = 113
                            INNER JOIN
                        `ActionProperty_OrgStructure` ON ActionProperty.id = `ActionProperty_OrgStructure`.`id`
                            AND `ActionProperty`.`type_id` = 14370
                            INNER JOIN
                        OrgStructure ON ActionProperty_OrgStructure.value = OrgStructure.id
                            AND OrgStructure.id <> 28
                            INNER JOIN
                        Pac_prb ON Pac_prb.id = Action.id
                            INNER JOIN
                        Event ON Event.id = Action.event_id
                            INNER JOIN
                        Client ON Client.id = Event.client_id
                    WHERE
                        `Action`.`deleted` = 0
                            AND ((Action.begDate >= CONCAT('{0}', ' 08:00:00')
                            AND Action.begDate <= CONCAT('{1}', ' 07:59:59')))
                    '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query)

    def get_priemn_umerlo(self, start, end):
        query = '''SELECT
                      `Action`.`begDate` AS `Datapost`,
                      Client.lastName,
                      Client.firstName,
                      Client.patrName,
                      Event.externalId,
                      OrgStructure.Address,
                      rbResult.name as result
                    FROM `Action`
                     INNER JOIN `ActionProperty`
                        ON `Action`.`id` = `ActionProperty`.`action_id` AND `Action`.`actionType_id` = 118
                    INNER  JOIN `ActionProperty_OrgStructure`
                        ON ActionProperty.id = `ActionProperty_OrgStructure`.`id` AND `ActionProperty`.`type_id` = 36081
                     INNER JOIN OrgStructure
                        ON ActionProperty_OrgStructure.value = OrgStructure.id
                      INNER JOIN Event
                      ON Event.id = Action.event_id
                      INNER JOIN rbResult
                      ON rbResult.id = Event.result_id AND rbResult.id IN(18, 38, 58, 69)
                      INNER JOIN Client
                      ON Client.id = Event.client_id
                    WHERE `Action`.`deleted` = 0
                    AND (Action.endDate >= '{0} 08:00:00' AND Action.endDate <= '{1} 07:59:59')
                    '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query)


class More_Then_21(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_more_then_21(self):
        query = '''
                    SELECT
                       Event.externalId,
                       Client.lastName,
                       Client.firstName,
                       Client.patrName,
                       Client.birthDate,
                       Event.setDate,
                       Action.begDate,
                       datediff(curdate(), Action.begDate) AS "Days",
                       OrgStructure.name AS "OrgStructureName"
                        FROM Action
                        INNER JOIN Event
                        ON Event.id = Action.event_id

                        INNER JOIN EventType
                          ON EventType.id = Event.eventType_id AND EventType.purpose_id = 8

                        INNER JOIN Client
                        ON Client.id = Event.client_id

                        INNER JOIN ActionProperty
                        ON Action.id = ActionProperty.action_id

                        INNER JOIN ActionProperty_HospitalBed
                        ON ActionProperty.id = ActionProperty_HospitalBed.id

                        INNER JOIN OrgStructure_HospitalBed
                        ON ActionProperty_HospitalBed.value = OrgStructure_HospitalBed.id

                        INNER JOIN OrgStructure
                        ON OrgStructure_HospitalBed.master_id = OrgStructure.id

                        WHERE
                          Action.deleted = 0
                          AND Event.deleted = 0
                          AND (Action.begDate <= curdate()
                          AND Action.endDate IS NULL)
                          AND (datediff(curdate(), Action.begDate) >= 21)
                        ORDER BY
                          OrgStructure_HospitalBed.master_id
                '''
        return self.db_session.execute(query)


class AnaesthesiaAmount(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_anaesthesia_amount(self, start, end):
        query = '''
                    SELECT
                        vid_Anest1.value AS type,
                        time(time(VK_anest1.value) - time(VN_anest1.value)) AS duration,
                        Ekstr_anest.Ekstrennost AS ekstr,
                        count(Action.id) as amount
                    FROM
                        Event
                            INNER JOIN
                        Action ON Action.event_id = Event.id
                            AND Action.deleted = 0
                            AND (Action.endDate >= CONCAT('{0}', ' 00:00:00')
                            AND Action.begDate < CONCAT('{1}', ' 23:59:59'))
                            LEFT JOIN
                        vid_Anest1 ON vid_Anest1.`Action.id` = Action.id
                            LEFT JOIN
                        VN_anest1 ON VN_anest1.`Action.id` = Action.id
                            LEFT JOIN
                        VK_anest1 ON VK_anest1.`Action.id` = Action.id
                            LEFT JOIN
                        Ekstr_anest ON Ekstr_anest.ID = Action.id
                    WHERE
                        Event.deleted = 0
                            AND Action.actionType_id = 1451
                    GROUP BY vid_Anest1.value , time(time(VK_anest1.value) - time(VN_anest1.value)) , Ekstr_anest.Ekstrennost;
                '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)


class List_Of_Operations(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_list_of_operations(self, start, end):
        query = u'''
                    SELECT
                        Client.lastName,
                        Client.firstName,
                        Client.patrName,
                        Client.birthDate,
                        if(Client.sex = 1, 'М', 'Ж') AS Pol,
                        date(Event.setDate) AS Data_otkrytiya,
                        Event.externalId,
                        Action.begDate AS Data_vremya_protokola,
                        poN.n AS Nomer_operacii,
                        poname.name AS Naimenovanie_operacii,
                        mkbd.mkb AS mkb,
                        ekstr.ekstr,
                        cel.cel AS Cel_operacii,
                        type.type AS Tip_operacii,
                        profile.profile AS Profil_operacii,
                        pobl.obl AS Oblast_operacii,
                        poblgo.poblgo AS Oblast_oper_god_ot4et,
                        zno.zno AS po_povodu_zno,
                        dsdo.ds AS ds_do_operacii,
                        mo.mo AS mo,
                        ina.ina,
                        dsafter.ds AS ds_posle_operacii,
                        morf.morf,
                        osl.osl,
                        rbFinance.name AS Isto4nik_finans
                    FROM
                        `Action`
                            INNER JOIN
                        Event ON Event.id = `Action`.event_id
                            AND `Action`.actionType_id = 127
                            AND (Action.begDate BETWEEN CONCAT('{0}', ' 08:00:00') AND CONCAT('{1}', ' 07:59:59'))
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            INNER JOIN
                        rbFinance ON rbFinance.id = EventType.finance_id
                            INNER JOIN
                        Client ON Client.id = Event.client_id
                            AND client_id <> 18
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_Integer.value AS N
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 4666
                        JOIN ActionProperty_Integer ON ActionProperty.id = ActionProperty_Integer.id) AS poN ON poN.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS cel
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1600443
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS cel ON cel.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS type
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1600444
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS type ON type.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS name
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 20692
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS poname ON poname.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS profile
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 3912090
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS profile ON profile.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS obl
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 10489
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS pobl ON pobl.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS poblgo
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 3912091
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS poblgo ON poblgo.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS zno
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 3912093
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS zno ON zno.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS ds
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1600445
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS dsdo ON dsdo.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS ds
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1748
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS dsafter ON dsafter.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, MKB.DiagID AS mkb
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 3912089
                        JOIN ActionProperty_MKB ON ActionProperty.id = ActionProperty_MKB.id
                        INNER JOIN MKB ON MKB.id = ActionProperty_MKB.value) AS mkbd ON mkbd.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS ekstr
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1600761
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS ekstr ON ekstr.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS mo
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 6527
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS mo ON mo.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS morf
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 3913452
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS morf ON morf.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS ina
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1600446
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS ina ON ina.id = `Action`.id
                            LEFT JOIN
                        (SELECT
                            Action.id, ActionProperty_String.value AS osl
                        FROM
                            Action
                        JOIN ActionProperty ON Action.id = ActionProperty.action_id
                            AND Action.deleted = 0
                        JOIN ActionPropertyType ON ActionProperty.type_id = ActionPropertyType.id
                            AND ActionPropertyType.id = 1800
                        JOIN ActionProperty_String ON ActionProperty.id = ActionProperty_String.id) AS osl ON osl.id = `Action`.id
                    WHERE
                        `Action`.deleted = 0
                            AND Event.deleted = 0
                    ORDER BY setDate;
                '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)


class Policlinic(object):

    def __init__(self):
        self.db_session = get_lpu_session()
        self.db_session2 = get_lpu_session()

    def __del__(self):
        self.db_session.close()
        self.db_session2.close()

    def __get_t21005oms(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Event`.`execPerson_id` AS `execPerson_id`
                    FROM
                        ((((`Event`
                        JOIN `Client` ON (((`Client`.`id` = `Event`.`client_id`)
                            AND (((year(`Event`.`setDate`) - year(`Client`.`birthDate`)) - (date_format(curdate(), '%m%d') < date_format(`Client`.`birthDate`, '%m%d'))) < 18))))
                        JOIN `Person` ON ((`Person`.`id` = `Event`.`execPerson_id`)))
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `rbSpeciality` ON ((`Person`.`speciality_id` = `rbSpeciality`.`id`)))
                    WHERE
                        `Event`.`eventType_id` = 109
                            AND Person.id = {0}
                            AND (`Event`.`setDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Event`.`setDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`
                    ORDER BY `rbSpeciality`.`name`
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def __get_polip(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Event`.`execPerson_id` AS `execPerson_id`
                    FROM
                        ((((`Event`
                        JOIN `Client` ON ((`Client`.`id` = `Event`.`client_id`)))
                        JOIN `Person` ON ((`Person`.`id` = `Event`.`execPerson_id`)))
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `rbSpeciality` ON ((`Person`.`speciality_id` = `rbSpeciality`.`id`)))
                    WHERE
                        Person.id = {0}
                            AND `Event`.`eventType_id` = 61
                            AND (`Event`.`setDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Event`.`setDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`
                    ORDER BY `rbSpeciality`.`name`;
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def __get_polib(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Event`.`execPerson_id` AS `execPerson_id`
                    FROM
                        ((((`Event`
                        JOIN `Client` ON ((`Client`.`id` = `Event`.`client_id`)))
                        JOIN `Person` ON ((`Person`.`id` = `Event`.`execPerson_id`)))
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `rbSpeciality` ON ((`Person`.`speciality_id` = `rbSpeciality`.`id`)))
                    WHERE
                        `Event`.`eventType_id` = 70
                            AND Person.id = {0}
                            AND (`Event`.`setDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Event`.`setDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`
                    ORDER BY `rbSpeciality`.`name`;
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def __get_poliz(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Event`.`execPerson_id` AS `execPerson_id`
                    FROM
                        ((((`Event`
                        JOIN `Client` ON ((`Client`.`id` = `Event`.`client_id`)))
                        JOIN `Person` ON ((`Person`.`id` = `Event`.`execPerson_id`)))
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `rbSpeciality` ON ((`Person`.`speciality_id` = `rbSpeciality`.`id`)))
                    WHERE
                        Person.id = {0}
                            AND `Event`.`eventType_id` = 65
                            AND (`Event`.`setDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Event`.`setDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`
                    ORDER BY `rbSpeciality`.`name`;
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def __get_zaochb(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Event`.`execPerson_id` AS `execPerson_id`
                    FROM
                        ((((`Event`
                        JOIN `Client` ON ((`Client`.`id` = `Event`.`client_id`)))
                        JOIN `Person` ON ((`Person`.`id` = `Event`.`execPerson_id`)))
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `rbSpeciality` ON ((`Person`.`speciality_id` = `rbSpeciality`.`id`)))
                    WHERE
                        Person.id = {0}
                            AND `Event`.`eventType_id` = 66
                            AND (`Event`.`setDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Event`.`setDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`
                    ORDER BY `rbSpeciality`.`name`;
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))

        return self.db_session.execute(query).first()

    def __get_kskons(self, id, start, end):
        query = u'''
                    SELECT
                        count(0) AS `number`,
                        `rbSpeciality`.`name` AS `speciality`,
                        `Action`.`person_id` AS `person_id`
                    FROM
                        ((((((`Event`
                        JOIN `EventType` ON ((`Event`.`eventType_id` = `EventType`.`id`)))
                        JOIN `Action` ON ((`Event`.`id` = `Action`.`event_id`)))
                        JOIN `ActionType` ON ((`Action`.`actionType_id` = `ActionType`.`id`)))
                        JOIN `Client` ON ((`Client`.`id` = `Event`.`client_id`)))
                        LEFT JOIN `Person` ON ((`Person`.`id` = `Action`.`person_id`)))
                        JOIN `rbSpeciality` ON ((`rbSpeciality`.`id` = `Person`.`speciality_id`)))
                    WHERE
                        Person.id = {0}
                            AND `EventType`.`purpose_id` = 8
                            AND `ActionType`.`group_id` IN (101 , 2036, 2037, 2477, 2478)
                            AND (`Action`.`endDate` >= CONCAT('{1}', ' 00:00:00')
                            AND `Action`.`endDate` <= CONCAT('{2}', ' 23:59:59'))
                            AND `Event`.`deleted` = 0
                            AND `Action`.`deleted` = 0
                    GROUP BY `rbSpeciality`.`name` , `Person`.`lastName`;
                    '''.format(id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query).first()

    def get_personpoly(self, start, end):
        query = u'''
                    SELECT
                        Person.id,
                        Person.lastName,
                        Person.firstName,
                        rbSpeciality.name as speciality
                    FROM
                        Person
                            INNER JOIN
                        rbSpeciality ON rbSpeciality.id = Person.speciality_id
                            AND (Person.orgStructure_id = 42
                            OR Person.orgStructure_id = 45
                            OR Person.id IN (216 , 457, 488))
                    WHERE
                        Person.speciality_id NOT IN (1 , 29, 30, 31, 32, 66, 67, 83)
                    ORDER BY Person.lastName;
                    '''
        result = self.db_session2.execute(query)
        data = list()
        for person in result:
            data.append(dict(person=person,
                             oms=self.__get_t21005oms(person.id, start, end),
                             polip=self.__get_polip(person.id, start, end),
                             polib=self.__get_polib(person.id, start, end),
                             poliz=self.__get_poliz(person.id, start, end),
                             zaochb=self.__get_zaochb(person.id, start, end),
                             kskons=self.__get_kskons(person.id, start, end),))
        return data


class Discharged_Patients(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_vypis(self, start, end):
        query = u'''SELECT
                        c.lastName,
                        c.firstName,
                        c.patrName,
                        if(c.sex = 1, 'М', 'Ж') AS 'Pol',
                        c.birthDate,
                        (year(Event.setDate) - year(c.birthDate)) - (DATE_FORMAT(Event.setDate, '%m%d') < DATE_FORMAT(c.birthDate, '%m%d')) AS age,
                        post.postdate,
                        date(p.begd) as begd,
                        date(Action.endDate) as vypis_date,
                        date(vypiska.begDate) as vypiska,
                        Event.externalId,
                        DS_osnk_zak_epic.value AS 'OsnovnoyKD',
                        DS_zak_epic.DiagID AS 'MKB',
                        DS_zak_epic.DiagName AS 'Diagnos'
                    FROM
                        Action
                            INNER JOIN
                        ActionType ON Action.`actionType_id` = ActionType.`id`
                            INNER JOIN
                        ActionProperty ON Action.`id` = ActionProperty.`action_id`
                            INNER JOIN
                        ActionProperty_HospitalBed ON ActionProperty.`id` = ActionProperty_HospitalBed.`id`
                            INNER JOIN
                        OrgStructure_HospitalBed ON ActionProperty_HospitalBed.`value` = OrgStructure_HospitalBed.`id`
                            INNER JOIN
                        Event ON Action.`event_id` = Event.`id`
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            INNER JOIN
                        (SELECT
                            Action.event_id AS evid, date(Action.endDate) AS postdate
                        FROM
                            Action
                        WHERE
                            Action.actionType_id = 112
                                AND Action.deleted = 0) AS post ON post.evid = Action.event_id
                            INNER JOIN
                        (SELECT
                            A.event_id AS evd, A.begDate AS begd
                        FROM
                            (SELECT
                            min(Action.id) id, event_id, begdate
                        FROM
                            Action
                        JOIN ActionType ON Action.actionType_id = ActionType.id
                        WHERE
                            ActionType.flatCode = 'moving'
                                AND Action.deleted = 0
                        GROUP BY event_id) A) AS p ON p.evd = Action.event_id
                            LEFT JOIN
                        (SELECT
                            Action.event_id AS evd, Action.begDate
                        FROM
                            Action
                        WHERE
                            Action.deleted = 0
                                AND Action.actionType_id = 118) AS vypiska ON vypiska.evd = Action.event_id
                            LEFT JOIN
                        DS_osnk_zak_epic ON Action.event_id = DS_osnk_zak_epic.event_id
                            LEFT JOIN
                        DS_zak_epic ON Action.event_id = DS_zak_epic.event_id
                            INNER JOIN
                        (SELECT
                            Action.id, ActionProperty_HospitalBedProfile.value
                        FROM
                            Action
                        INNER JOIN ActionType ON Action.`actionType_id` = ActionType.`id`
                        INNER JOIN ActionProperty ON Action.`id` = ActionProperty.`action_id`
                        INNER JOIN ActionPropertyType ON ActionPropertyType.`id` = ActionProperty.`type_id`
                        INNER JOIN ActionProperty_HospitalBedProfile ON ActionProperty.`id` = ActionProperty_HospitalBedProfile.`id`
                        INNER JOIN rbHospitalBedProfile ON ActionProperty_HospitalBedProfile.`value` = rbHospitalBedProfile.`id`
                        WHERE
                            (ActionType.`flatCode` = 'moving')
                                AND (ActionPropertyType.`code` = 'hospitalBedProfile')
                                AND (date(Action.endDate) >= date('{0}')
                                AND date(Action.endDate) <= date('{1}'))) sz ON Action.id = sz.id
                            INNER JOIN
                        Client c ON c.id = Event.client_id
                    WHERE
                        (date(Action.endDate) >= date('{0}')
                            AND date(Action.endDate) <= date('{1}'))
                            AND (ActionType.`flatCode` = 'moving')
                            AND (Action.`deleted` = 0)
                            AND (Event.`deleted` = 0)
                            AND (ActionProperty.`deleted` = 0)
                            AND (Action.id IN (SELECT
                                id
                            FROM
                                (SELECT
                                    max(Action.id) id
                                FROM
                                    Action
                                JOIN ActionType ON Action.actionType_id = ActionType.id
                                WHERE
                                    ActionType.flatCode = 'moving'
                                        AND Action.begDate IS NOT NULL
                                        AND Action.deleted = 0
                                GROUP BY event_id) A))
                            AND Action.event_id NOT IN (SELECT
                                e.id
                            FROM
                                Event e
                                    INNER JOIN
                                rbResult ON rbResult.id = e.result_id
                                    AND rbResult.name = 'умер')
                    ORDER BY Event.externalId
                    '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)


class Sickness_Rate_Blocks(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_sickness_rate_blocks(self, start, end):
        query = '''
                    SELECT
                        MKB.BlockName, MKB.BlockID, count(MKB.BlockID) AS amount
                    FROM
                        Event
                            INNER JOIN
                        Client ON Client.id = Event.client_id
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            INNER JOIN
                        rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
                            AND rbEventTypePurpose.id = 8
                            INNER JOIN
                        Diagnostic ON Diagnostic.event_id = Event.id
                            INNER JOIN
                        Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
                            AND Diagnosis.diagnosisType_id IN (1 , 2, 3, 5, 12, 13)
                            INNER JOIN
                        MKB ON MKB.DiagID = Diagnosis.MKB
                    WHERE
                        Event.deleted = 0
                            AND Event.execDate BETWEEN '{0} 00:00:00' AND '{1} 23:59:59'
                            AND Diagnosis.deleted = 0
                            AND Diagnostic.deleted = 0
                    GROUP BY MKB.BlockName , MKB.BlockID
                    ORDER BY MKB.BlockID
                '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)


class Paid_Patients(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_platn_ks(self):
        query = '''SELECT
                      Client.lastName,
                      Client.firstName,
                      Client.patrName,
                      Event.externalId,
                      Event.setDate,
                      Pac_prb.name AS otd,
                     rbFinance.name AS finance_source,
                      EventType.name AS event_type

                      FROM Event

                    INNER JOIN Client
                    ON Client.id = Event.client_id AND Event.deleted =0

                     INNER JOIN Pac_prb
                     ON Pac_prb.Evid = Event.id

                       INNER JOIN EventType
                      ON EventType.id = Event.eventType_id AND EventType.finance_id IN (4,9)

                      LEFT
                      JOIN rbFinance
                      ON rbFinance.id = EventType.finance_id

                      WHERE Event.execDate IS NULL

                      ORDER
                       BY Client.lastName, Pac_prb.Prb,rbFinance.name'''
        return self.db_session.execute(query)


class Sickness_Rate_Diagnosis(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_vypds(self, diagnosis, start, end):
        query = u'''SELECT Client.lastName
                               , Client.firstName
                              ,  Client.patrName
                              , DS_zak_epic.DiagID
                         , otd_vypis_from_dvizh.NAME as otd_vypis
                         , Event.externalid
                         , date(Event.setDate) as setDate
                         , date(otd_vypis_from_dvizh.endDate) as endDate

                    FROM
                      DS_zak_epic

                    INNER JOIN Event
                    ON Event.id = DS_zak_epic.event_id AND DS_zak_epic.DiagID = '{0}'

                    INNER JOIN otd_vypis_from_dvizh
                    ON otd_vypis_from_dvizh.EventID = DS_zak_epic.event_id
                    AND (otd_vypis_from_dvizh.endDate BETWEEN '{1} 00:00:00' AND '{2} 23:59:59')

                    INNER JOIN Client
                    ON Client.id = Event.client_id
                '''.format(diagnosis, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)


class Diag_Divergence(object):

    def __init__(self):
        self.db_session = get_lpu_session()

    def __del__(self):
        self.db_session.close()

    def get_divergence(self, start, end):
        query = u'''
                    SELECT
                        Event.externalId,
                        Client.lastName,
                        Client.firstName,
                        Client.patrName,
                        Client.birthDate,
                        Diagnosis.MKB,
                        DS.DiagID
                    FROM
                        Event
                            INNER JOIN
                        Client ON Client.id = Event.client_id
                            INNER JOIN
                        Diagnostic ON Diagnostic.event_id = Event.id
                            INNER JOIN
                        Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
                            AND Diagnosis.diagnosisType_id IN (1 , 2)
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            LEFT JOIN
                        (SELECT
                            Action.event_id AS 'ID',
                                ActionProperty_MKB.value AS 'ds',
                                MKB.DiagID
                        FROM
                            Action
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.deleted = 0
                            AND Action.actionType_id IN (139 , 2456)
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_MKB ON ActionProperty.id = ActionProperty_MKB.id
                            AND ActionProperty.type_id IN (1600022 , 245603)
                        INNER JOIN MKB ON ActionProperty_MKB.value = MKB.id) AS DS ON DS.ID = Event.id
                    WHERE
                        Event.setDate >= CONCAT('{0}', ' 00:00:00')
                            AND Event.setDate <= CONCAT('{1}', ' 23:59:59')
                            and Diagnosis.deleted = 0
                            and Diagnostic.deleted = 0
                            AND Event.deleted = 0
                            AND Diagnosis.MKB <> ''
                            AND DS.DiagID <> ''
                            AND (Diagnosis.MKB <> DS.DiagID)
                    GROUP BY Event.id
                    ORDER BY Client.lastName , Event.setDate;
                '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)

    def get_divergence1(self, start, end):
        query = u'''
                    SELECT
                        Event.externalId,
                        Client.lastName,
                        Client.firstName,
                        Client.patrName,
                        Client.birthDate,
                        MKB.DiagID AS 'MKB1',
                        DS.DiagID AS 'MKB2'
                    FROM
                        Event
                            INNER JOIN
                        Client ON Client.id = Event.client_id
                            INNER JOIN
                        Diagnostic ON Diagnostic.event_id = Event.id
                            INNER JOIN
                        Action ON Action.event_id = Event.id
                            INNER JOIN
                        ActionType ON ActionType.id = Action.actionType_id
                            AND Action.deleted = 0
                            AND Action.actionType_id = 112
                            INNER JOIN
                        ActionProperty ON Action.id = ActionProperty.action_id
                            INNER JOIN
                        ActionProperty_MKB ON ActionProperty.id = ActionProperty_MKB.id
                            AND ActionProperty.type_id = 1604
                            INNER JOIN
                        MKB ON ActionProperty_MKB.value = MKB.id
                            INNER JOIN
                        EventType ON EventType.id = Event.eventType_id
                            AND EventType.purpose_id = 8
                            LEFT JOIN
                        (SELECT
                            Action.event_id AS 'ID',
                                ActionProperty_MKB.value AS 'ds',
                                MKB.DiagID
                        FROM
                            Action
                        JOIN ActionType ON ActionType.id = Action.actionType_id
                            AND Action.deleted = 0
                            AND Action.actionType_id IN (139 , 2456)
                        INNER JOIN ActionProperty ON Action.id = ActionProperty.action_id
                        INNER JOIN ActionProperty_MKB ON ActionProperty.id = ActionProperty_MKB.id
                            AND ActionProperty.type_id IN (1600022 , 245603)
                        INNER JOIN MKB ON ActionProperty_MKB.value = MKB.id) AS DS ON DS.ID = Event.id
                    WHERE
                        Event.setDate >= CONCAT('{0}', ' 00:00:00')
                            AND Event.setDate <= CONCAT('{1}', ' 23:59:59')
                            and Diagnostic.deleted = 0
                            AND Event.deleted = 0
                            AND ActionProperty_MKB.value <> ''
                            AND DS.DiagID <> ''
                            AND MKB.DiagID <> ''
                            AND (MKB.DiagID <> DS.DiagID)
                    GROUP BY Event.id
                    ORDER BY Client.lastName , Event.setDate;
                '''.format(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        return self.db_session.execute(query)