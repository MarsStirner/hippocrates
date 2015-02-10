# -*- encoding: utf-8 -*-
from datetime import datetime

from flask import render_template, abort, request, url_for
from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import Sickness_Rate_Blocks
from application.lib.utils import public_endpoint


@public_endpoint
@module.route('/sickness_rate_blocks/', methods=['GET', 'POST'])
def sickness_rate_blocks():
    try:
        errors = list()
        sickness_rate_blocks = None
        if request.method == 'POST':
            try:
                data_obj = Sickness_Rate_Blocks()
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
                    sickness_rate_blocks = data_obj.get_sickness_rate_blocks(start, end)

        return render_template('reports/sickness_rate_blocks/index.html',
                               form=Form(),
                               sickness_rate_blocks=sickness_rate_blocks,
                               errors=errors)
    except TemplateNotFound:
        abort(404)