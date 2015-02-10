# -*- encoding: utf-8 -*-
from flask import render_template, abort, url_for, current_app
from jinja2 import TemplateNotFound

from ..app import module
from ..lib.data import Paid_Patients
from application.lib.utils import public_endpoint


def datetimeformat(value, format='%Y-%m-%d'):
    return value.strftime(format)


@public_endpoint
@module.route('/paid/', methods=['GET', 'POST'])
def paid():
    current_app.jinja_env.filters['datetimeformat'] = datetimeformat
    try:
        errors = list()
        data = None
        try:
            data_obj = Paid_Patients()
        except AttributeError, e:
            errors.append(
                u'<strong>Не настроено подключение к БД ЛПУ.</strong> '
                u'Заполните <a href="{}">настройки</a> подключения.'.format(url_for('.settings')))
        else:
            data = data_obj.get_platn_ks()
        return render_template('reports/paid/index.html',
                               data=data,
                               errors=errors)
    except TemplateNotFound:
        abort(404)