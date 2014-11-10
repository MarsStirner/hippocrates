# -*- coding: utf-8 -*-

from application.systemwide import db
from application.models.exists import Person, vrbPersonWithSpeciality
from flask.ext.login import UserMixin, AnonymousUserMixin, current_user
import hashlib


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
    def can_delete_event(event):
        return event and (
            current_user.has_right('adm', 'evtDelAll') or (
                current_user.has_right('evtDelOwn') and (
                    current_user.id == event.execPerson_id or
                    current_user.id == event.createPerson_id)))

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
        return False and action_type and (
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