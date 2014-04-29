# -*- encoding: utf-8 -*-
from flask import render_template, abort
from jinja2 import TemplateNotFound
from ..app import module

# noinspection PyUnresolvedReferences
from . import api_json


@module.route('/')
def index():
    try:
        return render_template('event/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/event.html')
def html_event_info():
    # event_id = int(request.args['event_id'])
    return render_template(
        'event/event_info.html'
    )


@module.route('/event_new.html')
def new_event():
    return render_template('event/new_event.html')