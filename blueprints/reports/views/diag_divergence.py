# -*- encoding: utf-8 -*-
from datetime import datetime
from flask import render_template, abort, request, url_for

from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import Diag_Divergence
from application.lib.utils import public_endpoint


@public_endpoint
@module.route('/diag_divergence/', methods=['GET', 'POST'])
def diag_divergence():
    try:
        errors = list()
        diag_divergence = None
        diag_divergence1 = None
        if request.method == 'POST':
            try:
                data_obj = Diag_Divergence()
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
                    diag_divergence = data_obj.get_divergence(start, end)
                    diag_divergence1 = data_obj.get_divergence1(start, end)
        return render_template('reports/diag_divergence/index.html',
                               form=Form(),
                               diag_divergence=diag_divergence,
                               diag_divergence1=diag_divergence1,
                               errors=errors)
    except TemplateNotFound:
        abort(404)