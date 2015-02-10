# -*- encoding: utf-8 -*-
from datetime import datetime

from flask import render_template, abort, request, url_for
from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import Patients_Process
from application.lib.utils import public_endpoint


@public_endpoint
@module.route('/patients_process/', methods=['GET', 'POST'])
def patients_process():
    try:
        errors = list()
        priemn_postup = None
        priemn_vypis = None
        priemn_perevod = None
        priemn_umerlo = None
        if request.method == 'POST':
            try:
                data_obj = Patients_Process()
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
                    priemn_postup = data_obj.get_priemn_postup(start, end)
                    priemn_vypis = data_obj.get_priemn_vypis(start, end)
                    priemn_perevod = data_obj.get_priemn_perevod(start, end)
                    priemn_umerlo = data_obj.get_priemn_umerlo(start, end)
        return render_template('reports/patients_process/index.html',
                               form=Form(),
                               priemn_postup=priemn_postup,
                               priemn_vypis=priemn_vypis,
                               priemn_perevod=priemn_perevod,
                               priemn_umerlo=priemn_umerlo,
                               errors=errors)
    except TemplateNotFound:
        abort(404)