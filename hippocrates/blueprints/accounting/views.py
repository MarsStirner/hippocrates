# -*- coding: utf-8 -*-
from .app import module
from blueprints.event.lib.utils import integration_1codvd_enabled
from flask import render_template


@module.route('/cashbook')
def cashbook_html():
    if integration_1codvd_enabled():
        return render_template('accounting/no_cashier_ui.html')
    return render_template('accounting/cashbook.html')


@module.route('/cashbook_operations')
def cashbook_operations():
    if integration_1codvd_enabled():
        return render_template('accounting/no_cashier_ui.html')
    return render_template('accounting/cashbook_operations.html')