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
        return render_template('sample/index.html')
    except TemplateNotFound:
        abort(404)