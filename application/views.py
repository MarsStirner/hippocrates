# -*- encoding: utf-8 -*-
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
from forms import LoginForm


login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser


@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated()

    if (request.endpoint and
            'static' not in request.endpoint and
            not login_valid and
            not current_user.is_admin() and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):
        return redirect(url_for('login', next=url_for(request.endpoint)))


@roles_require('admin')
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
            return redirect(request.args.get('next') or url_for('index'))
        else:
            errors.append(u'Неверная пара логин/пароль')

    return render_template('user/login.html', form=form, errors=errors)


@app.route('/logout/')
def logout():
    # Remove the user information from the session
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type', 'hippo_user'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return redirect(request.args.get('next') or '/')


@app.route('/api/rb/')
@app.route('/api/rb/<name>')
@cache.memoize(600)  # 86400
def api_refbook(name):
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
    for role in getattr(identity.user, 'roles', []):
        identity.provides.add(RoleNeed(role))
    for right in getattr(identity.user, 'rights', []):
        identity.provides.add(ActionNeed(right))
