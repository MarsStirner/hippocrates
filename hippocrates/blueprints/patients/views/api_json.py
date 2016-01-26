# -*- coding: utf-8 -*-

import datetime
import logging

from flask import abort, request

from nemesis.systemwide import db
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import jsonify, parse_id, public_endpoint, safe_int, safe_traverse, safe_traverse_attrs
from blueprints.patients.app import module
from nemesis.lib.sphinx_search import SearchPatient
from nemesis.lib.jsonify import ClientVisualizer
from nemesis.models.client import Client, ClientFileAttach, ClientDocument, ClientPolicy, ClientContact
from nemesis.models.exists import FileMeta, FileGroupDocument
from blueprints.patients.lib.utils import (set_client_main_info, ClientSaveException, add_or_update_doc,
    add_or_update_address, add_or_update_copy_address, add_or_update_policy, add_or_update_blood_type,
    add_or_update_allergy, add_or_update_intolerance, add_or_update_soc_status, add_or_update_relation,
    add_or_update_contact, generate_filename, save_new_file, delete_client_file_attach_and_relations,
    add_or_update_work_soc_status
)


__author__ = 'mmalkov'

logger = logging.getLogger('simple')


@module.route('/api/search_clients.json')
def api_search_clients():
    try:
        query_string = request.args['q']
        limit = int(request.args.get('limit', 100))
    except (KeyError, ValueError):
        return abort(404)

    base_query = Client.query.outerjoin(ClientPolicy, ClientDocument, ClientContact)
    id_list = []

    if query_string:
        result = SearchPatient.search(query_string, limit)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            base_query = base_query.filter(Client.id.in_(id_list))
        else:
            return jsonify([])
    clients = base_query.order_by(db.func.field(Client.id, *id_list)).all()
    context = ClientVisualizer()
    if 'short' in request.args:
        return jsonify(map(context.make_short_client_info, clients))
    else:
        return jsonify(map(context.make_search_client_info, clients))


@module.route('/api/patient.json')
def api_patient_get():
    client_id = parse_id(request.args, 'client_id')
    if client_id is False:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return abort(404)

        if 'for_servicing' in request.args:
            return jsonify(context.make_client_info_for_servicing(client))
        elif 'short' in request.args:
            return jsonify(context.make_short_client_info(client))
        return jsonify({
            'client_data': context.make_client_info(client)
        })
    else:
        client = Client()
        # db.session.add(client)  # требуется привязанный к сессии клиент для доступа к некоторым атрибутам (documents)
        return jsonify({
            'client_data': context.make_client_info(client)
        })


@module.route('/api/patient_events.json', methods=['GET'])
@api_method
def api_patient_events_get():
    client_id = parse_id(request.args, 'client_id')
    vsl = ClientVisualizer()
    client = Client.query.get(client_id)
    return {
        'info': client,
        'events': vsl.make_events(client)
    }


@module.route('/api/appointments.json')
@public_endpoint
def api_patient_appointments():
    client_id = parse_id(request.args, 'client_id')
    every = request.args.get('every', False)
    if client_id is False:
        return abort(404)
    context = ClientVisualizer()
    if client_id:
        if Client.query.filter(Client.id == client_id).count():
            return jsonify(context.make_appointments(client_id, every))
        else:
            return abort(404)
    return jsonify(None, 400, 'Can\'t!')


@module.route('/api/save_patient_info.json', methods=['POST'])
@api_method
def api_patient_save():
    client_data = request.json
    client_id = parse_id(client_data, 'client_id', True)
    if client_id is False:
        raise ApiException(404, u'Пациент %s не найден' % client_id)

    err_msg = u'Ошибка сохранения данных пациента'
    if client_id:
        client = Client.query.get(client_id)
        client_info = client_data.get('info')
        if client_info:
            client = set_client_main_info(client, client_info)
            db.session.add(client)
    else:
        client = Client()
        client_info = client_data.get('info')
        if not client_info:
            raise ClientSaveException(err_msg, u'Отсутствует основная информация о пациенте.')
        client = set_client_main_info(client, client_info)
        db.session.add(client)

    id_doc_info = client_data.get('id_docs')
    if id_doc_info:
        for id_doc in id_doc_info:
            doc = add_or_update_doc(client, id_doc)
            db.session.add(doc)

    reg_addr_info = client_data.get('reg_addresses')
    actual_reg_address = None
    if reg_addr_info:
        for reg_addr in reg_addr_info:
            ra = add_or_update_address(client, reg_addr)
            if ra.deleted != 1 and ra.deleted != 2:
                actual_reg_address = ra
            db.session.add(ra)

    live_addr_info = client_data.get('live_addresses')
    if live_addr_info:
        for live_addr in live_addr_info:
            same_as_reg = live_addr.get('synced', False)
            if same_as_reg:
                la = add_or_update_copy_address(client, live_addr, actual_reg_address)
            else:
                la = add_or_update_address(client, live_addr)
            db.session.add(la)

    cpol_info = client_data.get('compulsory_policies')
    if cpol_info:
        for cpol in cpol_info:
            pol = add_or_update_policy(client, cpol)
            db.session.add(pol)

    vpol_info = client_data.get('voluntary_policies')
    if vpol_info:
        for vpol in vpol_info:
            pol = add_or_update_policy(client, vpol)
            db.session.add(pol)

    blood_type_info = client_data.get('blood_types')
    if blood_type_info:
        for bt in blood_type_info:
            bt = add_or_update_blood_type(client, bt)
            db.session.add(bt)

    allergy_info = client_data.get('allergies')
    if allergy_info:
        for allergy in allergy_info:
            alg = add_or_update_allergy(client, allergy)
            db.session.add(alg)

    intolerance_info = client_data.get('intolerances')
    if intolerance_info:
        for intolerance in intolerance_info:
            intlr = add_or_update_intolerance(client, intolerance)
            db.session.add(intlr)

    works_info = client_data.get('works')
    if works_info:
        for w in works_info:
            work = add_or_update_work_soc_status(client, w)
            db.session.add(work)

    ss_info = client_data.get('invalidities')
    if ss_info:
        for ss in ss_info:
            sstat = add_or_update_soc_status(client, ss)
            db.session.add(sstat)

    ss_info = client_data.get('nationalities')
    if ss_info:
        for ss in ss_info:
            sstat = add_or_update_soc_status(client, ss)
            db.session.add(sstat)

    relation_info = client_data.get('relations')
    if relation_info:
        for relation in relation_info:
            rel = add_or_update_relation(client, relation)
            db.session.add(rel)

    contact_info = client_data.get('contacts')
    if contact_info:
        for contact in contact_info:
            cont = add_or_update_contact(client, contact)
            db.session.add(cont)

    db.session.commit()

    return int(client)

# for tests without external kladr
@module.route('/api/kladr_city.json', methods=['GET'])
def api_kladr_city_get():
    from nemesis.models.kladr_models import Kladr
    val = request.args['city']
    res = Kladr.query.filter(Kladr.NAME.startswith(val)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])


@module.route('/api/kladr_street.json', methods=['GET'])
def api_kladr_street_get():
    from nemesis.models.kladr_models import Street
    city = request.args['city']
    street = request.args['street']
    res = Street.query.filter(Street.CODE.startswith(city[:-2]), Street.NAME.startswith(street)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])


@module.route('/api/client_file_attach.json')
@api_method
def api_patient_file_attach():
    data = request.args
    cviz = ClientVisualizer()

    fm_id = safe_int(data.get('file_meta_id'))
    cfa_id = safe_int(data.get('cfa_id'))
    if not (cfa_id or fm_id):
        raise ApiException(404, u'Не передано поле cfa_id или поле file_meta_id')
    if fm_id:
        fm = FileMeta.query.get(fm_id)
        if not fm:
            raise ApiException(404, u'Не найдена запись FileMeta с id = {0}'.format(fm_id))
        return cviz.make_file_info(fm)
    elif cfa_id:
        cfa_query_result = ClientFileAttach.query.join(
            FileGroupDocument
        ).filter(
            ClientFileAttach.id == cfa_id,
        ).first()
        if not cfa_query_result:
            raise ApiException(404, u'Не найдены данные для записи ClientFileAttach с id = {0}'.format(cfa_id))
        cfa = cviz.make_file_attach_info(cfa_query_result, False, [])

        file_pages = db.session.query(
            FileMeta.id, FileMeta.idx
        ).select_from(ClientFileAttach).join(
            FileGroupDocument, FileMeta
        ).filter(
            ClientFileAttach.id == cfa_id,
            FileMeta.deleted == 0
        ).all()
        file_pages = [dict(id=fm_id, idx=idx) for fm_id, idx in file_pages]

        return {
            'cfa': cfa,
            'file_pages': file_pages
        }


@module.route('/api/client_file_attach.json', methods=['POST'])
@api_method
def api_patient_file_attach_save():
    data = request.json
    cviz = ClientVisualizer()
    client_id = safe_int(data.get('client_id'))
    if not client_id:
        raise ApiException(404, u'Не передано поле client_id')
    file_attach = data.get('file_attach')
    if not file_attach:
        raise ApiException(404, u'Не передано поле file_attach')
    file_document = file_attach.get('file_document')
    if not file_document:
        raise ApiException(404, u'Не передано поле file_attach.file_document')
    document_name = file_document.get('name')
    doc_type = file_attach.get('doc_type')
    doc_type_id = safe_traverse(doc_type, 'id')
    relation_type = file_attach.get('relation_type')
    relation_type_id = safe_traverse(relation_type, 'id')

    cfa_id = file_attach.get('id')
    if cfa_id:
        cfa = ClientFileAttach.query.get(cfa_id)
        if not cfa:
            raise ApiException(404, u'Не найдена запись ClientFileAttach с id = {0}'.format(cfa_id))
        cfa.documentType_id = doc_type_id
        cfa.relationType_id = relation_type_id
        db.session.add(cfa)

        fgd = cfa.file_document
        fgd.name = document_name
        db.session.add(fgd)
    else:
        attach_date = file_attach.get('attach_date') or datetime.datetime.now()

        fgd = FileGroupDocument()
        fgd.name = document_name
        cfa = ClientFileAttach()
        cfa.client_id = client_id
        cfa.attachDate = attach_date
        cfa.documentType_id = doc_type_id
        cfa.relationType_id = relation_type_id
        cfa.file_document = fgd
        db.session.add(fgd)
        db.session.add(cfa)

    document_id = safe_traverse(file_attach, 'document_info', 'id')
    policy_id = safe_traverse(file_attach, 'policy_info', 'id')
    if document_id:
        c_doc = ClientDocument.query.get(document_id)
        if not c_doc:
            raise ApiException(404, u'Не найдена запись ClientDocument с id = {0}'.format(document_id))
        c_doc.file_attach = cfa
        db.session.add(c_doc)
    elif policy_id:
        c_pol = ClientPolicy.query.get(policy_id)
        if not c_pol:
            raise ApiException(404, u'Не найдена запись ClientDocument с id = {0}'.format(policy_id))
        c_pol.file_attach = cfa
        db.session.add(c_pol)

    db.session.commit()

    f_descname = safe_traverse_attrs(cfa, 'documentType', 'name')
    f_relation_type = safe_traverse_attrs(cfa, 'relationType', 'leftName')
    file_pages = file_document.get('files', [])
    for page_idx, file_page in enumerate(file_pages):
        f_meta = file_page.get('meta')
        if not f_meta:
            raise ApiException(404, u'Не передано поле meta в file_attach.file_document.files[{0}]'.format(page_idx))
        fm_id = f_meta.get('id')
        f_idx = safe_int(f_meta.get('idx')) or 0
        f_name = f_meta.get('name') or ''
        if fm_id:
            fm = FileMeta.query.get(fm_id)
            if not fm:
                raise ApiException(404, u'Не найдена запись FileMeta с id = {0}'.format(fm_id))
            fm.name = f_name
            fm.idx = f_idx
            db.session.add(fm)
        else:
            f_file = file_page.get('file')
            if not f_file:
                raise ApiException(404, u'Не передано поле file в file_attach.file_document.files[{0}]'.format(page_idx))
            f_mime = f_file.get('mime')
            attach_date = cfa.attachDate
            filename = generate_filename(f_name, f_mime, date=attach_date) if f_name else (
                generate_filename(None, f_mime, descname=f_descname, idx=f_idx, date=attach_date, relation_type=f_relation_type)
            )
            ok, msg = save_new_file(file_page, filename, fgd, client_id)
            if not ok:
                raise ApiException(500, msg)
        db.session.commit()

    return {
        'cfa': cviz.make_file_attach_info(cfa, False)
    }


@module.route('/api/client_file_attach.json', methods=['DELETE'])
@api_method
def api_patient_file_attach_delete():
    data = request.args
    cfa_id = safe_int(data.get('cfa_id'))
    fm_id = safe_int(data.get('file_meta_id'))
    if not (cfa_id or fm_id):
        raise ApiException(404, u'Не передано поле cfa_id или поле file_meta_id')
    if cfa_id:
        delete_client_file_attach_and_relations(cfa_id)
    elif fm_id:
        fm = FileMeta.query.get(fm_id)
        if not fm:
            raise ApiException(404, u'Не найдена запись FileMeta с id = {0}'.format(fm_id))
        fm.deleted = 1
        db.session.add(fm)
        FileMeta.query.filter(FileMeta.idx > fm.idx, FileMeta.deleted == 0).update({
            'idx': FileMeta.idx - 1
        })
        db.session.commit()