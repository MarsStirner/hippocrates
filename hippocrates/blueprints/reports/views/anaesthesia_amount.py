__author__ = 'plakrisenko'
# -*- encoding: utf-8 -*-
from datetime import datetime
from flask import render_template, abort, request, redirect, url_for

from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import AnaesthesiaAmount
from nemesis.lib.utils import public_endpoint


@module.route('/anaesthesia_amount/', methods=['GET', 'POST'])
@public_endpoint
def anaesthesia_amount():
    try:
        errors = list()
        anaesthesia_amount = None
        if request.method == 'POST':
            try:
                data_obj = AnaesthesiaAmount()
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
                    anaesthesia_amount = data_obj.get_anaesthesia_amount(start, end)

        return render_template('reports/anaesthesia_amount/index.html',
                               form=Form(),
                               anaesthesia_amount=anaesthesia_amount,
                               errors=errors)
    except TemplateNotFound:
        abort(404)