# -*- coding: utf-8 -*-

from flask import render_template
from .app import module


@module.route('/cashbook')
def cashbook_html():
    return render_template('accounting/cashbook.html')


@module.route('/contract-list')
def html_contract_list():
    return render_template('accounting/contract_list.html')