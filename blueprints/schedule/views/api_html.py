# -*- coding: utf-8 -*-
from flask import request, abort, render_template
from application.lib.utils import public_endpoint
from blueprints.schedule.app import module
from blueprints.schedule.models.exists import Client
from blueprints.schedule.views.jsonify import ClientVisualizer, Format

__author__ = 'mmalkov'


@module.route('/api/patient.html')
@public_endpoint
def html_patient():
    try:
        client_id = int(request.args['client_id'])
    except KeyError or ValueError:
        return abort(404)
    client = Client.query.get(client_id)
    if not client:
        return abort(404)
    context = ClientVisualizer(Format.HTML)
    return render_template(
        'schedule/patient_info.html',
        client=client,
        client_info_codes_rus={
            'id': u'Код пациента',
            'birthDate': u'Дата рождения',
            'regAddress': u'Адрес регистрации',
            'liveAddress': u'Адрес проживания',
            'SNILS': u'СНИЛС',
            'nameText': u'ФИО',
            'sex': u'Пол',
            'document': u'Документ',
            'contact': u'Контакты',
            'voluntaryPolicy': u'Полис ДМС',
            'compulsoryPolicy': u'Полис ОМС'
        },
        client_info_codes_order=['id', 'nameText', 'birthDate', 'sex', 'regAddress', 'liveAddress', 'document', 'compulsoryPolicy', 'voluntaryPolicy', 'SNILS', 'contact'],
        record_codes_rus={
            'mark': u'Отметка',
            'begDateTime': u'Дата и время приёма',
            'office': u'Кабинет',
            'person': u'Специалист',
            'createPerson': u'Записал',
            'note': u'Примечания'
        },
        record_codes_order=['mark', 'begDateTime', 'office', 'person', 'createPerson', 'note'],
        clientData=context.make_client_info(client),
        records=context.make_records(client),
    )