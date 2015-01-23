# -*- coding: utf-8 -*-
from .app import module
from flask import render_template


@module.route('/cashbook')
def cashbook_html():
    return render_template('accounting/cashbook.html')


@module.route('/cashbook_operations')
def cashbook_operations():
    return render_template('accounting/cashbook_operations.html')