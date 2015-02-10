# -*- encoding: utf-8 -*-
from datetime import datetime
from flask import render_template, abort, request, redirect, url_for

from jinja2 import TemplateNotFound
from flask.ext.wtf import Form

from ..app import module
from ..lib.data import List_Of_Operations
from application.lib.utils import public_endpoint


@public_endpoint
@module.route('/list_of_operations/', methods=['GET', 'POST'])
def list_of_operations():
    try:
        errors = list()
        list_of_operations = None
        if request.method == 'POST':
            try:
                data_obj = List_Of_Operations()
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
                    list_of_operations = data_obj.get_list_of_operations(start, end)

        return render_template('reports/list_of_operations/index.html',
                               form=Form(),
                               list_of_operations=list_of_operations,
                               errors=errors)
    except TemplateNotFound:
        abort(404)