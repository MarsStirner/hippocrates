# -*- coding: utf-8 -*-
from flask import render_template, abort, redirect, url_for, flash
from jinja2 import TemplateNotFound
from wtforms import TextField, IntegerField
from wtforms.validators import Required
from flask.ext.wtf import Form

from ..app import module
from ..models import ConfigVariables
from application.systemwide import db
from application.utils import admin_permission
from application.lib.utils import public_endpoint
from ..lib.data import Statistics


@module.route('/')
@public_endpoint
def index():
    try:
        errors = list()
        full_number = None
        postup = None
        vypis = None
        pat_org = None
        try:
            data_obj = Statistics()
        except AttributeError, e:
            errors.append(
                u'<strong>Не настроено подключение к БД ЛПУ.</strong> '
                u'Заполните <a href="{}">настройки</a> подключения.'.format(url_for('.settings')))
        else:
            full_number = data_obj.get_patients()
            postup = data_obj.get_postup()
            vypis = data_obj.get_vypis()

        return render_template('reports/index.html',
                               full_number=full_number,
                               postup=postup,
                               vypis=vypis,
                               pat_org=pat_org,
                               errors=errors)
    except TemplateNotFound:
        abort(404)


@public_endpoint
@module.route('/ajax_pat_otd/', methods=['GET', 'POST'])
def ajax_statistic():
    pat_org = None
    hospitalizations_by_fs = None
    hosp_figures = None
    errors = list()
    try:
        data_obj = Statistics()
    except AttributeError, e:
        errors.append(
            u'<strong>Не настроено подключение к БД ЛПУ.</strong> '
            u'Заполните <a href="{}">настройки</a> подключения.'.format(url_for('.settings')))
    else:
        pat_org = data_obj.get_patients_orgStruct()
        hospitalizations_by_fs = data_obj.get_hospitalizations_by_fs()
        hosp_figures = data_obj.get_hospitalization_figures()
    return render_template('reports/statistic.html',
                           pat_org=pat_org,
                           hosp_by_fs=hospitalizations_by_fs,
                           hosp_figures=hosp_figures,
                           errors=errors)


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
            form[variable.code].value = variable.value if variable.value else ""

        if form.validate_on_submit():
            for variable in variables:
                variable.value = form.data[variable.code]
            db.session.commit()
            flash(u'Настройки изменены')
            return redirect(url_for('.settings'))

        return render_template('reports/settings.html', form=form)
    except TemplateNotFound, e:
        abort(404)