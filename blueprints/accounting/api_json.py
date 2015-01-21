# -*- coding: utf-8 -*-

from flask import request
from .app import module
from application.systemwide import db
from application.models.event import Event, EventPayment
from application.models.enums import PaymentType
from application.lib.utils import jsonify, parse_id, safe_traverse, safe_date


@module.route('/api/event_payment/make_payment.json', methods=['POST'])
def api_event_make_payment():
    pay_data = request.json
    event_id = parse_id(pay_data, 'event_id')
    if not event_id:
        return jsonify(u'Отсутствует номер обращения event_id', 422, 'ERROR')
    payment_date = safe_date(pay_data.get('payment_date'))
    if not payment_date:
        return jsonify(u'Отсутствует дата платежа payment_date', 422, 'ERROR')
    cash_operation = safe_traverse(pay_data.get('cash_operation'), 'id')
    payment_type = safe_traverse(pay_data.get('payment_type'), 'id', default=PaymentType.cash[0])
    payment_sum = pay_data.get('payment_sum')
    if not payment_sum:
        return jsonify(u'Отсутствует сумма платежа payment_sum', 422, 'ERROR')
    new_act = pay_data.get('new_act')

    event = Event.query.get(event_id)
    # новый платеж
    payment = EventPayment()
    payment.master_id = event_id
    payment.date = payment_date
    payment.cashOperation_id = cash_operation
    payment.sum = payment_sum
    payment.typePayment = payment_type
    payment.cashBox = ''
    payment.sumDiscount = 0
    payment.action_id = None
    payment.service_id = None
    event.payments.append(payment)

    # обновить номер акта через костыль
    if new_act:
        local_contract = event.localContract
        local_contract.coordText = new_act

    db.session.add(event)
    db.session.commit()

    return jsonify(None)