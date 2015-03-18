# -*- encoding: utf-8 -*-

import traceback
import logging

from flask import render_template, abort, request, url_for, send_file, g
from jinja2 import TemplateNotFound

from app import module
from nemesis.lib.utils import jsonify, crossdomain, public_endpoint
from blueprints.print_subsystem.lib.internals import RenderTemplateException
from blueprints.print_subsystem.models.models_all import Rbprinttemplate
from lib.data import Print_Template


PER_PAGE = 20
xml_encodings = ['windows-1251', 'utf-8']


@module.errorhandler(RenderTemplateException)
@crossdomain('*', methods=['POST', 'OPTIONS'], headers='Content-Type')
def handle_render_template_error(err):
    name = u'Ошибка формирования шаблона печати для документа "%s". Свяжитесь с администратором.' % err.data['template_name']
    err_msg = err.message
    detailed_msg = u'\n'.join([
        u'%s' % {
            RenderTemplateException.Type.syntax: u'Ошибка в синтаксисе шаблона, строка %s' % err.data.get('lineno'),
            RenderTemplateException.Type.other: u'Ошибка на сервере печати'
        }[err.data['type']]
    ])
    return jsonify({
        'name': name,
        'data': {
            'err_msg': err_msg,
            'detailed_msg': detailed_msg,
            'trace': err.data.get('trace')
        }
    }, 500, 'error')


@module.route('/')
def index():
    try:
        return render_template('{0}/index.html'.format(module.name))
    except TemplateNotFound:
        abort(404)


@public_endpoint
@module.route('/print_template', methods=["POST", "OPTIONS"])
@crossdomain('*', methods=['POST', 'OPTIONS'], headers='Content-Type')
def print_templates_post():
    data = request.get_json()
    if data.get('separate', True):
        separator = '\n\n<div style="page-break-after: always" ></div>\n\n'
    else:
        separator = '\n\n'

    try:
        result = [
            Print_Template().print_template(doc)
            for doc in data.get('documents', [])
        ]
    except RenderTemplateException, e:
        raise e
    except Exception, e:
        logging.critical('error in rendering', exc_info=True)
        raise RenderTemplateException(e.message, {
            'type': RenderTemplateException.Type.other,
            'template_name': '',
            'trace': unicode(traceback.format_exc(), 'utf-8')
        })

    font_url_eot = url_for(".fonts", filename="free3of9.eot", _external=True)
    font_url_woff = url_for(".fonts", filename="free3of9.woff", _external=True)
    font_url_ttf = url_for(".fonts", filename="free3of9.ttf", _external=True)
    font_url_svg = url_for(".fonts", filename="free3of9.svg", _external=True)
    font_url_ttf128 = url_for(".fonts", filename="code128.ttf", _external=True)
    template_style = url_for(".static", filename="css/template_style.css", _external=True)
    # converted original free3of9.ttf font with http://www.fontsquirrel.com/tools/webfont-generator
    style = u'''
<style>
    @font-face {
        font-family: 'free3of9';
        src: url('%s');
        src: url('%s?#iefix') format('embedded-opentype'),
             url('%s') format('woff'),
             url('%s') format('truetype'),
             url('%s#free3of9') format('svg');
        font-weight:normal;
        font-style:normal
    }
    @font-face {
        font-family: 'code128';
        src: url('%s') format('truetype');
        font-weight:normal;
        font-style:normal
    }
</style>
<link rel="stylesheet" href="%s"/>
''' % (font_url_eot, font_url_eot, font_url_woff, font_url_ttf, font_url_svg, font_url_ttf128, template_style)
    return style + separator.join(result)


@public_endpoint
@module.route('/fonts')
@module.route('/fonts/<filename>')
@crossdomain('*', methods=['GET'])
def fonts(filename=None):
    return send_file('../blueprints/print_subsystem/static/%s' % filename)


@module.route('/templates/')
@module.route('/templates/<context>.json')
@public_endpoint
@crossdomain('*', methods=['GET'])
def api_templates(context=None):
    # Не пора бы нам от этой ерунды избавиться?
    # Неа, нам нужно подключение к разным БД (http://stackoverflow.com/questions/7923966/flask-sqlalchemy-with-dynamic-database-connections)
    # А в Гиппократе всё работает. Там те же две БД.
    if not context:
        return jsonify(None)
    templates = g.printing_session.query(Rbprinttemplate).filter(Rbprinttemplate.context == context)
    return jsonify([{
        'id': t.id,
        'code': t.code,
        'name': t.name,
        'meta': t.meta_data,
    } for t in templates])
