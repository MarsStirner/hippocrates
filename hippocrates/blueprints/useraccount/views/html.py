# -*- coding: utf-8 -*-
from flask import render_template

from ..app import module

__author__ = 'viruzzz-kun'


@module.route('/')
def index_html():
    return render_template('useraccount/index.html')

