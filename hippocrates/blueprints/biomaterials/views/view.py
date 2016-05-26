# -*- coding: utf-8 -*-
from flask import render_template

from hippocrates.blueprints.biomaterials.app import module

# noinspection PyUnresolvedReferences
from . import api_json

__author__ = 'plakrisenko'


@module.route('/')
def index_html():
    return render_template('biomaterials/index.html')