# -*- encoding: utf-8 -*-
from datetime import datetime

from flask import render_template, abort, request, url_for
from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import Policlinic
from nemesis.lib.utils import public_endpoint


@public_endpoint
@module.route('/policlinic/', methods=['GET', 'POST'])
def policlinic():
    try:
        errors = list()
        data = None
        if request.method == 'POST':
            try:
                data_obj = Policlinic()
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
                    data = data_obj.get_personpoly(start, end)
        return render_template('reports/policlinic/index.html',
                               form=Form(),
                               data=data,
                               errors=errors)
    except TemplateNotFound:
        abort(404)