# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, redirect, url_for, flash, session, current_app
from flask.views import MethodView

from jinja2 import TemplateNotFound
from wtforms import TextField, PasswordField, IntegerField
from flask_wtf import Form
from wtforms.validators import Required
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed
from flask.ext.principal import identity_loaded, Permission, RoleNeed, UserNeed
from flask.ext.login import login_user, logout_user, login_required, current_user

from application.app import app, db, login_manager
from application.context_processors import general_menu
from models import Users, Roles
from lib.user import User
from forms import LoginForm
from lib.utils import admin_permission, public_endpoint


login_manager.login_view = 'login'


@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated()

    if (request.endpoint and
            'static' not in request.endpoint and
            not login_valid and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):
        return redirect(url_for('login', next=url_for(request.endpoint)))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/', methods=['GET', 'POST'])
@public_endpoint
def login():
    # login form that uses Flask-WTF
    form = LoginForm()
    errors = list()

    # Validate form input
    if form.validate_on_submit():
        # Retrieve the user from the hypothetical datastore

        # TODO: переделать под работу с  БД
        if form.login.data.strip() == 'admin' and form.password.data.strip() == 'admin':
            user = User('admin')
            user.id = 1
            login_user(user, force=True)

            # Tell Flask-Principal the identity changed
            identity_changed.send(current_app._get_current_object(), identity=Identity(1))

            return redirect(request.args.get('next') or url_for('index'))
        else:
            errors.append(u'Неверная пара логин/пароль')


        # user = db.session.query(Users).filter(Users.login == form.login.data.strip()).first()
        # if user:
        #     check_user = User(user.login)
        #     # Compare passwords (use password hashing production)
        #     if check_user.check_password(form.password.data.strip(), user.password):
        #         # Keep the user info in the session using Flask-Login
        #         login_user(user)
        #
        #         # Tell Flask-Principal the identity changed
        #         identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        #
        #         return redirect(request.args.get('next') or url_for('index'))
        #     else:
        #         errors.append(u'Неверная пара логин/пароль')
        # else:
        #     errors.append(u'Нет пользователя с логином <b>%s</b>' % form.login.data.strip())

    return render_template('user/login.html', form=form, errors=errors)


@app.route('/logout/')
def logout():
    # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    return redirect(request.args.get('next') or '/')


@app.errorhandler(403)
def authorisation_failed(e):
    flash(u'У вас недостаточно привилегий для доступа к функционалу')
    return render_template('user/denied.html')


#########################################

@login_manager.user_loader
def load_user(user_id):
    # Return an instance of the User model
    # return db.session.query(Users).get(user_id)
    return User('admin')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    if identity.id:
        identity.user = load_user(identity.id)

        # Add the UserNeed to the identity
        if hasattr(identity.user, 'id'):
            identity.provides.add(UserNeed(identity.user.id))

        # Assuming the User model has a list of roles, update the
        # identity with the roles that the user provides
        if hasattr(identity.user, 'roles'):
            for role in identity.user.roles:
                identity.provides.add(RoleNeed(role.code))