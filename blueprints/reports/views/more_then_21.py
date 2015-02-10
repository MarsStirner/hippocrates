# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, url_for
from jinja2 import TemplateNotFound

from ..app import module
from ..lib.data import More_Then_21
from application.lib.utils import public_endpoint


@public_endpoint
@module.route('/more_then_21/', methods=['GET', 'POST'])
def more_then_21():
    try:
        errors = list()
        more_then_21 = None
        if request.method == 'GET':
            try:
                data_obj = More_Then_21()
                more_then_21 = [1, 2]
            except AttributeError, e:
                errors.append(
                    u'<strong>Не настроено подключение к БД ЛПУ.</strong> '
                    u'Заполните <a href="{}">настройки</a> подключения.'.format(url_for('.settings')))
            else:
                more_then_21 = data_obj.get_more_then_21()
        return render_template('reports/more_then_21/index.html',
                               more_then_21=more_then_21,
                               errors=errors)
    except TemplateNotFound:
        abort(404)