# -*- encoding: utf-8 -*-

import requests

from flask import render_template, abort, request, redirect, url_for, flash, session, current_app
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed
from flask.ext.principal import identity_loaded, Permission, RoleNeed, UserNeed, ActionNeed
from flask.ext.login import login_user, logout_user, login_required, current_user

from application.app import app, db, login_manager, cache
from application.context_processors import *
from application.models.exists import rbPrintTemplate
from .lib.utils import public_endpoint, jsonify, roles_require, rights_require, request_wants_json
from application.models import *
from lib.user import UserAuth, AnonymousUser
from forms import LoginForm, RoleForm


login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser


@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated()

    if (request.endpoint and
            'static' not in request.endpoint and
            not current_user.is_admin() and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):

        if not login_valid:
            return redirect(url_for('login', next=url_for(request.endpoint)))
        if not current_user.current_role:
            return redirect(url_for('select_role', next=url_for(request.endpoint)))


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
        user = UserAuth.auth_user(form.login.data.strip(), form.password.data.strip())
        if user:
            # Keep the user info in the session using Flask-Login
            login_user(user)
            # Tell Flask-Principal the identity changed
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
            return redirect(url_for('select_role', next=request.args.get('next')))
        else:
            errors.append(u'Неверная пара логин/пароль')

    return render_template('user/login.html', form=form, errors=errors)


@app.route('/select_role/', methods=['GET', 'POST'])
@public_endpoint
def select_role():
    form = RoleForm()

    errors = list()

    form.roles.choices = current_user.roles

    # Validate form input
    if form.is_submitted():
        current_user.current_role = form.roles.data
        identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        return redirect(request.args.get('next') or request.referrer or url_for('index'))
    return render_template('user/select_role.html', form=form, errors=errors)


@app.route('/logout/')
def logout():
    # Remove the user information from the session
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type', 'hippo_user', 'crumbs'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return redirect(request.args.get('next') or '/')


@app.route('/api/rb/')
@app.route('/api/rb/<name>')
@cache.memoize(600)  # 86400
def api_refbook(name):
    for mod in (enums,):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)
            res = jsonify(ref_book.rb()['objects'])
            return res
    for mod in (exists, schedule, actions, client, event):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)
            if 'deleted' in ref_book.__dict__:
                res = jsonify(ref_book.query.filter_by(deleted=0).order_by(ref_book.id).all())
            else:
                res = ref_book.query.order_by(ref_book.id).all()
                res = jsonify(res)
            return res
    return abort(404)


@app.route('/api/kladr/city/')
@app.route('/api/kladr/city/<search_query>/')
@cache.memoize(86400)
def kladr_city(search_query=None):
    result = []
    if search_query is None:
        return jsonify([])
    short_types = [u'г', u'п', u'с']
    response = requests.get(u'{0}/kladr/city/{1}/'.format(app.config['VESTA_URL'], search_query))
    for city in response.json()['data']:
        if city['shorttype'] in short_types:
            data = {'code': city['identcode'], 'name': u'{0}. {1}'.format(city['shorttype'], city['name'])}
            if city['parents']:
                for parent in city['parents']:
                    data['name'] = u'{0}, {1}. {2}'.format(data['name'], parent['shorttype'], parent['name'])
            result.append(data)
    return jsonify(result)


@app.route('/api/kladr/street/')
@app.route('/api/kladr/street/<city_code>/<search_query>/')
@cache.memoize(86400)
def kladr_street(city_code=None, search_query=None):
    result = []
    if city_code is None or search_query is None:
        return jsonify([])
    response = requests.get(u'{0}/kladr/street/{1}/{2}/'.format(app.config['VESTA_URL'], city_code, search_query))
    for street in response.json()['data']:
        data = {'code': street['identcode'], 'name': u'{0} {1}'.format(street['fulltype'], street['name'])}
        result.append(data)
    return jsonify(result)


@app.errorhandler(403)
def authorisation_failed(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=403, result_name=u'Forbidden')
    flash(u'У вас недостаточно привилегий для доступа к функционалу')
    return render_template('user/denied.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=404, result_name=u'Page not found')
    flash(u'Указанный вами адрес не найден')
    return render_template('404.html'), 404


#########################################

@login_manager.user_loader
def load_user(user_id):
    # Return an instance of the User model
    # Минимизируем количество обращений к БД за данными пользователя
    hippo_user = session.get('hippo_user', None)
    if not hippo_user:
        hippo_user = UserAuth.get_by_id(int(user_id))
        session['hippo_user'] = hippo_user
    # session['hippo_user'] = hippo_user
    return hippo_user


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(identity.user, 'id'):
        identity.provides.add(UserNeed(identity.user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    # for role in getattr(identity.user, 'roles', []):
    #     identity.provides.add(RoleNeed(role[0]))
    current_role = getattr(identity.user, 'current_role', None)
    if current_role:
        identity.provides = set()
        identity.provides.add(RoleNeed(identity.user.current_role))

    user_rights = getattr(identity.user, 'rights', None)
    if isinstance(user_rights, dict):
        for right in user_rights.get(current_role, []):
            identity.provides.add(ActionNeed(right))
