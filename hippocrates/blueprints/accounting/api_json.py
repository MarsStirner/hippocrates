# -*- coding: utf-8 -*-

from flask import request
from sqlalchemy import func

from .app import module
from nemesis.systemwide import db
from nemesis.models.event import Event, EventPayment, EventType
from nemesis.models.exists import Person, rbCashOperation
from nemesis.models.client import Client
from nemesis.models.enums import PaymentType
from nemesis.lib.utils import jsonify, parse_id, safe_traverse, safe_date
from nemesis.lib.jsonify import EventVisualizer


@module.route('/api/event_payment/make_payment.json', methods=['POST'])
def api_event_make_payment():
    pay_data = request.json
    event_id = parse_id(pay_data, 'event_id')
    if not event_id:
        return jsonify(u'Отсутствует номер обращения event_id', 422, 'ERROR')
    payment_date = safe_date(pay_data.get('payment_date'))
    if not payment_date:
        return jsonify(u'Отсутствует дата платежа payment_date', 422, 'ERROR')
    cash_operation_id = safe_traverse(pay_data.get('cash_operation'), 'id')
    cash_op = rbCashOperation.query.get(cash_operation_id) if cash_operation_id else None
    payment_type = safe_traverse(pay_data.get('payment_type'), 'id', default=PaymentType.cash[0])
    payment_sum = pay_data.get('payment_sum')
    if not payment_sum:
        return jsonify(u'Отсутствует сумма платежа payment_sum', 422, 'ERROR')
    if cash_op and cash_op.code == 'refund':
        payment_sum = -payment_sum

    new_act = pay_data.get('new_act')

    event = Event.query.get(event_id)
    # новый платеж
    payment = EventPayment()
    payment.master_id = event_id
    payment.date = payment_date
    payment.cashOperation_id = cash_operation_id
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


@module.route('/api/event_payment/get_payments.json', methods=["POST"])
def api_get_event_payments():
    flt = request.get_json()
    base_query = EventPayment.query.join(Event).filter(EventPayment.deleted == 0, Event.deleted == 0)
    context = EventVisualizer()

    if 'beg_date' in flt:
        base_query = base_query.filter(EventPayment.date >= safe_date(flt['beg_date']))
    if 'end_date' in flt:
        base_query = base_query.filter(EventPayment.date <= safe_date(flt['end_date']))
    if 'cashbox' in flt:
        base_query = base_query.filter(EventPayment.cashBox == flt['cashbox'])
    if 'cashier_person_id' in flt:
        base_query = base_query.filter(EventPayment.createPerson_id == flt['cashier_person_id'])
    if 'payment_type_id' in flt:
        base_query = base_query.filter(EventPayment.typePayment == flt['payment_type_id'])
    if 'cash_operation_id' in flt:
        base_query = base_query.filter(EventPayment.cashOperation_id == flt['cash_operation_id'])
    if 'event_purpose_id' in flt:
        base_query = base_query.join(EventType).filter(EventType.purpose_id == flt['event_purpose_id'])
    if 'event_type_id' in flt:
        base_query = base_query.filter(Event.eventType_id == flt['event_type_id'])
    if 'org_struct_id' in flt:
        base_query = base_query.join(Event.execPerson).filter(Person.orgStructure_id == flt['org_struct_id'])
    if 'exec_person_id' in flt:
        base_query = base_query.filter(Event.execPerson_id == flt['exec_person_id'])

    order_options = flt.get('sorting_params')
    if order_options:
        desc_order = order_options['order'] == 'DESC'
        col_name = order_options['column_name']
        if col_name == 'date':
            base_query = base_query.order_by(EventPayment.date.desc() if desc_order else EventPayment.date,
                                             EventPayment.id.desc() if desc_order else EventPayment.id)
        if col_name == 'cashbox':
            base_query = base_query.order_by(EventPayment.cashBox.desc() if desc_order else EventPayment.cashBox)
        elif col_name == 'cashier_name':
            base_query = base_query.outerjoin(EventPayment.createPerson).order_by(
                Person. lastName.desc() if desc_order else Person.lastName
            )
        elif col_name == 'cash_operation':
            base_query = base_query.outerjoin(rbCashOperation).order_by(
                rbCashOperation.name.desc() if desc_order else rbCashOperation.name
            )
        elif col_name == 'sum':
            base_query = base_query.order_by(EventPayment.sum.desc() if desc_order else EventPayment.sum,
                                             EventPayment.id.desc() if desc_order else EventPayment.id)
        elif col_name == 'client_name':
            base_query = base_query.outerjoin(Client).order_by(Client.lastName.desc() if desc_order else Client.lastName)
        elif col_name == 'client_bd':
            base_query = base_query.outerjoin(Client).order_by(Client.birthDate.desc() if desc_order else Client.birthDate)
        elif col_name == 'client_sex':
            base_query = base_query.outerjoin(Client).order_by(Client.sexCode.desc() if desc_order else Client.sexCode)
        elif col_name == 'event_type_name':
            base_query = base_query.outerjoin(EventType).order_by(
                EventType.name.desc() if desc_order else EventType.name
            )
        elif col_name == 'event_beg_date':
            base_query = base_query.order_by(Event.setDate.desc() if desc_order else Event.setDate)
        elif col_name == 'event_end_date':
            base_query = base_query.order_by(Event.execDate.desc() if desc_order else Event.execDate)
        elif col_name == 'event_exec_person_name':
            base_query = base_query.outerjoin(Event.execPerson).order_by(
                Person.lastName.desc() if desc_order else Person.lastName
            )
    else:
        base_query = base_query.order_by(EventPayment.date, EventPayment.id)

    metrics_query = base_query.with_entities(
        func.count(),
        func.sum(func.IF(EventPayment.sum > 0, EventPayment.sum, 0)),
        - func.sum(func.IF(EventPayment.sum < 0, EventPayment.sum, 0))
    )
    metrics = metrics_query.first()
    metrics = {
        'total': metrics[0],
        'income': metrics[1],
        'expense': metrics[2]
    }

    per_page = int(flt.get('per_page', 20))
    page = int(flt.get('page', 1))
    paginate = base_query.paginate(page, per_page, False)
    all_payment_id_list = base_query.with_entities(EventPayment.id).all()
    return jsonify({
        'pages': paginate.pages,
        'metrics': metrics,
        'items': [
            context.make_search_payments_list(event)
            for event in paginate.items
        ],
        'all_payment_id_list': all_payment_id_list
    })