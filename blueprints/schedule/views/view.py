# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, redirect, url_for, flash

from jinja2 import TemplateNotFound
from wtforms import TextField, BooleanField, IntegerField
from wtforms.validators import Required
from flask.ext.wtf import Form

from ..app import module
from application.database import db
from application.lib.utils import admin_permission, public_endpoint


@module.route('/')
@public_endpoint
def index():
    try:
        return render_template('schedule/index.html')
    except TemplateNotFound:
        abort(404)


@module.route('/doctors/')
@public_endpoint
def doctors():
    try:
        return render_template('schedule/doctors.html')
    except TemplateNotFound:
        abort(404)


@module.route('/patients/')
@public_endpoint
def patients():
    try:
        return render_template('schedule/patients.html')
    except TemplateNotFound:
        abort(404)