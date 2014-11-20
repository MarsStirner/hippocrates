# -*- coding: utf-8 -*-

import hashlib
from application.lib.utils import safe_traverse_attrs

from application.systemwide import db
from application.models.exists import Person, vrbPersonWithSpeciality
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user

from application.models.enums import ActionStatus
from application.lib.user_rights import (urEventPoliclinicPaidCreate, urEventPoliclinicOmsCreate,
    urEventPoliclinicDmsCreate, urEventDiagnosticPaidCreate, urEventDiagnosticBudgetCreate)


class User(UserMixin):

    def __init__(self, person):
        if not isinstance(person, Person):
            raise AttributeError(u'Not instance of models.Person')
        self.deleted = 0
        self.__dict__.update(dict((key, value)
                                  for key, value in person.__dict__.iteritems()
                                  if not callable(value) and not key.startswith('__')))
        self.roles = list()
        self._current_role = None
        self.rights = dict()
        self.post = dict()
        if person.post:
            self.post.update(dict((key, value)
                             for key, value in person.post.__dict__.iteritems()
                             if not callable(value) and not key.startswith('__')))
        self.set_roles_rights(person)

        orgStructure = person.org_structure
        atos = set()
        while orgStructure:
            atos.add(orgStructure.id)
            orgStructure = orgStructure.parent if orgStructure.inheritActionTypes else None
        self.action_type_org_structures = atos
        self.action_type_personally = []
        self.info = vrbPersonWithSpeciality.query.get(self.id)

    @property
    def current_role(self):
        return getattr(self, '_current_role', None)

    @current_role.setter
    def current_role(self, value):
        self._current_role = value
        from ..models.actions import ActionType_User
        from ..models.exists import rbUserProfile
        self.action_type_personally = [
            record.actionType_id
            for record in ActionType_User.query.outerjoin(rbUserProfile).filter(db.or_(
                ActionType_User.person_id == self.id,
                rbUserProfile.code == value
            ))
        ]
        self.current_rights = self.rights[value]

    def is_active(self):
        return self.deleted == 0

    def is_admin(self):
        return getattr(self, 'current_role', None) == 'admin'

    def role_in(self, *args):
        roles = []
        for arg in args:
            if isinstance(arg, list):
                roles.extend(arg)
            elif isinstance(arg, tuple):
                roles.extend(list(arg))
            else:
                roles.append(arg)
        return self.current_role in roles

    def has_role(self, role):
        # what about list?
        for r in self.roles:
            if r[0] == role:
                return True
        return False

    def has_right(self, *rights):
        current_rights = set(self.current_rights)
        return any((right in current_rights) for right in rights)

    def set_roles_rights(self, person):
        if person.user_profiles:
            for role in person.user_profiles:
                self.roles.append((role.code, role.name))
                if role.rights:
                    self.rights[role.code] = list()
                    for right in role.rights:
                        self.rights[role.code].append(right.code)

    def export_js(self):
        return {
            'id': self.get_id(),
            'roles': self.roles,
            'is_admin': self.is_admin(),
            'current_role': self.current_role,
            'rights': self.rights,
            'action_type_org_structures': sorted(getattr(self, 'action_type_org_structures', set())),
            'action_type_personally': sorted(getattr(self, 'action_type_personally', [])),
            'info': getattr(self, 'info', {})
        }


class AnonymousUser(AnonymousUserMixin):

    def is_admin(self):
        return False

    def export_js(self):
        return {
            'id': None,
            'roles': [],
            'is_admin': self.is_admin(),
            'current_role': None,
            'rights': [],
        }


class UserAuth():

    @classmethod
    def auth_user(cls, login, password):
        person = cls.__get_by_login(login)
        if person and cls.__check_password(person.password, password):
            return User(person)
        return None

    @classmethod
    def __get_by_login(cls, login):
        person = db.session.query(Person).filter(Person.login == login).first()
        if person:
            return person
        return None

    @classmethod
    def __check_password(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def __prepare_user(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_id(cls, user_id):
        return User(db.session.query(Person).get(int(user_id)))

    @classmethod
    def get_roles_by_login(cls, login):
        from ..models.exists import rbUserProfile, PersonProfiles
        return [
            {'code': role.code, 'name': role.name}
            for role in (rbUserProfile.query
                         .join(PersonProfiles)
                         .join(Person)
                         .filter(Person.login == login)
                         .order_by(rbUserProfile.name))
        ]


modeRights = (
    u'Assessment',
    u'Diagnostic',
    u'Treatment',
    u'Action'  # Общего плана, поступление-движение-выписка
)


class UserUtils(object):

    @staticmethod
    def can_create_event(event, out_msg=None):
        if out_msg is None:
            out_msg = {'message': u'ok'}

        base_msg = u'У пользователя нет прав на создание обращений типа %s'
        event_type = event and event.eventType
        if not event_type:
            out_msg['message'] = u'У обращения не указан тип'
            return False
        if current_user.has_right('adm'):
            return True
        # есть ли ограничения на создание обращений определенных EventType
        if event.is_policlinic and event.is_paid:
            if not current_user.has_right(urEventPoliclinicPaidCreate):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_oms:
            if not current_user.has_right(urEventPoliclinicOmsCreate):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
            client = event.client
            if client.is_adult:
                out_msg['message'] = u'Нельзя создавать обращения %s для пациентов старше 18 лет' % unicode(event_type)
                return False
            if not safe_traverse_attrs(client, 'reg_address', 'is_russian'):
                out_msg['message'] = u'Нельзя создавать обращения %s для пациентов без адреса ' \
                                     u'регистрации в РФ' % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_dms:
            if not current_user.has_right(urEventPoliclinicDmsCreate):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_diagnostic and event.is_paid:
            if not current_user.has_right(urEventDiagnosticPaidCreate):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_diagnostic and event.is_budget:
            if not current_user.has_right(urEventDiagnosticBudgetCreate):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        # все остальные можно
        return True

    @staticmethod
    def can_edit_event(event):
        return event and (
            current_user.has_right('adm') or (
                event.is_closed and
                current_user.id in (event.createPerson_id, event.execPerson_id) and
                current_user.has_right('evtEditClosed')
            ) or not event.is_closed)

    @staticmethod
    def can_delete_event(event, out_msg=None):
        if out_msg is None:
            out_msg = {'message': u'ok'}

        if not event:
            out_msg['message'] = u'Обращение еще не создано'
            return False
        if current_user.has_right('adm', 'evtDelAll'):
            return True
        elif current_user.has_right('evtDelOwn') and not event.is_closed:
            if event.execPerson_id == current_user.id:
                return True
            elif event.createPerson_id == current_user.id:
                if event.payments:
                    out_msg['message'] = u'В обращении есть платежи по услугам'
                    return False
                for action in event.actions:
                    # Проверка, что все действия не были изменены после создания обращения
                    # или, что не появилось новых действий
                    if action.modifyPerson_id != event.createPerson_id:
                        out_msg['message'] = u'В обращении были созданы новые или отредактированы первоначальные ' \
                                             u'документы'
                        return False
                    # не закрыто
                    if action.status == ActionStatus.finished[0]:
                        out_msg['message'] = u'В обращении есть закрытые документы'
                        return False
                    # не отмечено "Считать"
                    if action.account == 1:
                        out_msg['message'] = u'В обращении есть услуги, отмеченные для оплаты'
                        return False
                return True
        out_msg['message'] = u'У пользователя нет прав на удаление обращения'
        return False

    @staticmethod
    def can_close_event(event):
        return event and not event.is_closed and (
            current_user.has_right('adm') or (
                current_user.role_in('doctor', 'clinicDoctor') and
                current_user.id == event.execPerson_id
            ) or (
                current_user.role_in('rRegistartor', 'clinicRegistrator') and event.is_diagnostic and
                current_user.id == event.createPerson_id
            )
        )

    @staticmethod
    def can_delete_action(action):
        return action and (
            # админу можно всё
            current_user.has_right('adm') or (
                # остальным - только если обращение не закрыто
                not action.event.is_closed and (
                    # либо есть право на удаление любых действий
                    current_user.has_right('actDelAll') or (
                        # либо только своих
                        current_user.has_right('actDelOwn') and (
                            current_user.id in (action.createPerson_id, action.person_id))))))

    @staticmethod
    def can_create_action(at_id, event_id):
        from application.models.event import Event
        from application.models.actions import ActionType
        action_type = ActionType.query.get_or_404(at_id)
        event = Event.query.get_or_404(event_id)
        createRight = u'client%sCreate' % modeRights[action_type.class_]
        return action_type and (
            current_user.has_right('adm') or (
                not event.is_closed and current_user.has_right(createRight)))

    @staticmethod
    def can_edit_action(action):
        updateRight = u'client%sUpdate' % modeRights[action.actionType.class_]
        return action and (
            # админу можно всё
            current_user.has_right('adm') or (
                # действие не закрыто
                action.status < 2 and
                # остальным - только если обращение не закрыто
                not action.event.is_closed and (
                    # либо есть право редактировать любые действия
                    current_user.has_right('editOtherpeopleAction') or (
                        # либо право на свои определённых классов
                        current_user.has_right(updateRight) and
                        current_user.id in (action.createPerson_id, action.person_id)))))

    @staticmethod
    def can_read_action(action):
        readRight = u'client%sRead' % modeRights[action.actionType.class_]
        return action and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight) and
                current_user.id in (action.createPerson_id, action.person_id)))