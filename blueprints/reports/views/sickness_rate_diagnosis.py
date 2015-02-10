# -*- encoding: utf-8 -*-
from datetime import datetime

from flask import render_template, abort, request, url_for, current_app
from flask.ext.wtf import Form
from jinja2 import TemplateNotFound

from ..app import module
from ..lib.data import Sickness_Rate_Diagnosis
from application.lib.utils import public_endpoint


def datetimeformat(value, format='%Y-%m-%d'):
    return value.strftime(format)


@public_endpoint
@module.route('/sickness_rate_diagnosis/', methods=['GET', 'POST'])
def sickness_rate_diagnosis():
    current_app.jinja_env.filters['datetimeformat'] = datetimeformat
    try:
        errors = list()
        data = None
        if request.method == 'POST':
            try:
                data_obj = Sickness_Rate_Diagnosis()
            except AttributeError, e:
                errors.append(
                    u'<strong>Не настроено подключение к БД ЛПУ.</strong> '
                    u'Заполните <a href="{}">настройки</a> подключения.'.format(url_for('.settings')))
            else:
                try:
                    start = datetime.strptime(request.form['start'], '%d.%m.%Y')
                    end = datetime.strptime(request.form['end'], '%d.%m.%Y')
                except ValueError:
                    errors.append(u'Некорректно указаны даты')
                else:
                    if request.form['diagnosis']:
                        data = data_obj.get_vypds(request.form['diagnosis'], start, end)
                    else:
                        errors.append(u'Не указан диагноз')

        return render_template('reports/sickness_rate_diagnosis/index.html',
                               form=Form(),
                               data=data,
                               errors=errors)
    except TemplateNotFound:
        abort(404)