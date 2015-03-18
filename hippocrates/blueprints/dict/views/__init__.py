# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, redirect, url_for

from jinja2 import TemplateNotFound
from wtforms import TextField, BooleanField, IntegerField
from wtforms.validators import Required
from flask_wtf import Form

from ..app import module
from ..models import ConfigVariables
from nemesis.systemwide import db
from nemesis.utils import admin_permission


@module.route('/')
def index():
    try:
        return render_template('dict/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/settings/', methods=['GET', 'POST'])
@admin_permission.require(http_exception=403)
def settings():
    try:
        class ConfigVariablesForm(Form):
            pass

        variables = db.session.query(ConfigVariables).order_by('id').all()
        for variable in variables:
            if variable.value_type == "int":
                setattr(ConfigVariablesForm,
                        variable.code,
                        IntegerField(variable.code, validators=[Required()], default="", description=variable.name))
            else:
                setattr(ConfigVariablesForm,
                        variable.code,
                        TextField(variable.code, validators=[Required()], default="", description=variable.name))

        form = ConfigVariablesForm()
        for variable in variables:
            form[variable.code].value = variable.value

        if form.validate_on_submit():
            for variable in variables:
                variable.value = form.data[variable.code]
            db.session.commit()
            return redirect(url_for('.settings'))

        return render_template('dict/settings.html', form=form)
    except TemplateNotFound:
        abort(404)