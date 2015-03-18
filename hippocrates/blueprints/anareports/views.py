# -*- coding: utf-8 -*-
from .app import module
from flask import render_template

__author__ = 'viruzzz-kun'


@module.route('/')
def index_html():
    return render_template('anareports/index.html')