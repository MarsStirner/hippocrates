# -*- coding: utf-8 -*-

import datetime

from flask import abort, request

from nemesis.systemwide import db
from nemesis.lib.utils import jsonify, logger, parse_id, public_endpoint, safe_int, safe_traverse, safe_traverse_attrs
from blueprints.patients.app import module
from nemesis.lib.sphinx_search import SearchPatient
from nemesis.lib.jsonify import ClientVisualizer
from nemesis.models.client import Client, ClientFileAttach, ClientDocument, ClientPolicy
from nemesis.models.exists import FileMeta, FileGroupDocument
from blueprints.patients.lib.utils import (set_client_main_info, ClientSaveException, add_or_update_doc,
    add_or_update_address, add_or_update_copy_address, add_or_update_policy, add_or_update_blood_type,
    add_or_update_allergy, add_or_update_intolerance, add_or_update_soc_status, add_or_update_relation,
    add_or_update_contact, generate_filename, save_new_file, delete_client_file_attach_and_relations
)


__author__ = 'mmalkov'


@module.errorhandler(ClientSaveException)
def handle_client_error(err):
    return jsonify({
        'name': err.message,
        'data': {
            'err_msg': err.data
        }
    }, 422, 'error')


@module.route('/api/search_clients.json')
def api_search_clients():
    try:
        query_string = request.args['q']
        limit = int(request.args.get('limit', 100))
    except (KeyError, ValueError):
        return abort(404)

    base_query = Client.query
    id_list = []

    if query_string:
        result = SearchPatient.search(query_string)
        id_list = [item['id'] for item in result['result']['items']]
        if id_list:
            base_query = base_query.filter(Client.id.in_(id_list))
        else:
            return jsonify([])
    clients = base_query.order_by(db.func.field(Client.id, *id_list)).limit(limit).all()
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
def api_patient_save():
    client_data = request.json
    client_id = parse_id(client_data, 'client_id', True)
    if client_id is False:
        return abort(404)

    err_msg = u'Ошибка сохранения данных пациента'
    try:
        if client_id:
            client = Client.query.get(client_id)
            client_info = client_data.get('info')
            if client_info:
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

            ss_info = client_data.get('soc_statuses')
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

            ss_info = client_data.get('soc_statuses')
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

    #     for id_info in client_info['identifications']:
    #         if not 'id' in id_info:
    #             id_ext = get_new_identification(id_info)
    #             client.identifications.append(id_ext)
    #         else:
    #             id_ext = get_modified_identification(client, id_info)
    #             db.session.add(id_ext)
        db.session.commit()
    except ClientSaveException:
        raise
    except Exception, e:
        logger.error(e, exc_info=True)
        db.session.rollback()
        return jsonify(
            {
                'name': err_msg,
                'data': {
                    'err_msg': 'INTERNAL SERVER ERROR'
                }
            },
            500,
            'save client data error'
        )

    return jsonify(int(client))

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


@module.route('/api/client_file_attach.json', methods=['POST', 'GET', 'DELETE'])
def api_patient_file_attach():
    if request.method == 'GET':
        data = request.args
        cviz = ClientVisualizer()

        file_meta_id = safe_int(data.get('file_meta_id'))
        if file_meta_id:
            fm = FileMeta.query.get(file_meta_id)
            return jsonify(cviz.make_file_info(fm))
        else:
            cfa_id = safe_int(data.get('cfa_id'))
            idx = safe_int(data.get('idx')) or 0

            cfa_query_result = ClientFileAttach.query.join(
                FileGroupDocument
            ).outerjoin(
                FileMeta
            ).filter(
                ClientFileAttach.id == cfa_id,
            ).first()
            cfa = cviz.make_file_attach_info(cfa_query_result, True, [idx]) if cfa_query_result else None
            file_pages = db.session.query(
                FileMeta.id, FileMeta.idx
            ).select_from(ClientFileAttach).join(
                FileGroupDocument, FileMeta
            ).filter(
                ClientFileAttach.id == cfa_id,
                FileMeta.deleted == 0
            ).all()
            file_pages = [dict(id=fm_id, idx=idx) for fm_id, idx in file_pages]

            return jsonify({
                'cfa': cfa,
                'file_pages': file_pages
            })

    elif request.method == 'POST':
        data = request.json
        cviz = ClientVisualizer()
        client_id = safe_int(data.get('client_id'))
        file_attach = data.get('file_attach')
        if not file_attach:
            raise Exception
        cfa_id = file_attach.get('id')

        if cfa_id:
            doc_type = file_attach.get('doc_type')
            relation_type = file_attach.get('relation_type')

            document_id = safe_traverse(file_attach, 'document_info', 'id')
            policy_id = safe_traverse(file_attach, 'policy_info', 'id')

            cfa = ClientFileAttach.query.get(cfa_id)
            cfa.documentType_id = safe_traverse(doc_type, 'id')
            cfa.relationType_id = safe_traverse(relation_type, 'id')
            db.session.add(cfa)
            if document_id:
                c_doc = ClientDocument.query.get(document_id)
                c_doc.file_attach = cfa
                db.session.add(c_doc)
            elif policy_id:
                c_pol = ClientPolicy.query.get(policy_id)
                c_pol.file_attach = cfa
                db.session.add(c_pol)

            file_document = file_attach.get('file_document')
            document_name = file_document.get('name')
            fgd = cfa.file_document
            fgd.name = document_name
            db.session.add(fgd)

            file_pages = file_document.get('files')
            for file_page in file_pages:
                fm_id = safe_traverse(file_page, 'meta', 'id')
                f_idx = safe_int(safe_traverse(file_page, 'meta', 'idx')) or 0
                f_name = safe_traverse(file_page, 'meta', 'name') or ''
                if fm_id:
                    fm = FileMeta.query.get(fm_id)
                    fm.name = f_name
                    fm.idx = f_idx
                    db.session.add(fm)
                else:
                    f_mime = safe_traverse(file_page, 'file', 'mime')
                    attach_date = cfa.attachDate
                    f_descname = safe_traverse_attrs(cfa, 'documentType', 'name')
                    f_relation_type = safe_traverse_attrs(cfa, 'relationType', 'leftName')
                    filename = generate_filename(f_name, f_mime, date=attach_date) if f_name else (
                        generate_filename(None, f_mime, descname=f_descname, idx=f_idx, date=attach_date, relation_type=f_relation_type)
                    )
                    ok, msg = save_new_file(file_page, filename, fgd, client_id)
                    if not ok:
                        return jsonify(msg, 500, 'ERROR')
            try:
                db.session.commit()
            except Exception, e:
                # todo:
                raise
            result = cviz.make_file_attach_info(cfa, False)
            return jsonify({
                'cfa': result
            })

        else:
            attach_date = file_attach.get('attach_date') or datetime.datetime.now()
            doc_type = file_attach.get('doc_type')
            relation_type = file_attach.get('relation_type')

            document_id = safe_traverse(file_attach, 'document_info', 'id')
            policy_id = safe_traverse(file_attach, 'policy_info', 'id')

            file_document = file_attach.get('file_document')
            document_name = file_document.get('name')
            file_pages = file_document.get('files')

            fgd = FileGroupDocument()
            fgd.name = document_name
            cfa = ClientFileAttach()
            cfa.client_id = client_id
            cfa.attachDate = attach_date
            cfa.documentType_id = safe_traverse(doc_type, 'id')
            cfa.relationType_id = safe_traverse(relation_type, 'id')
            cfa.file_document = fgd
            db.session.add(fgd)
            if document_id:
                c_doc = ClientDocument.query.get(document_id)
                c_doc.file_attach = cfa
                db.session.add(c_doc)
            elif policy_id:
                c_pol = ClientPolicy.query.get(policy_id)
                c_pol.file_attach = cfa
                db.session.add(c_pol)
            db.session.add(cfa)
            try:
                db.session.commit()
            except Exception, e:
                # todo:
                raise

            f_descname = safe_traverse(doc_type, 'name', default=u'Файл')
            f_relation_type = safe_traverse(relation_type, 'leftName', default=u'')
            for file_page in file_pages:
                f_meta = file_page.get('meta')
                f_file = file_page.get('file')
                f_name = f_meta.get('name') or ''
                f_idx = f_meta.get('idx')
                f_mime = f_file.get('mime')

                filename = generate_filename(f_name, f_mime, date=attach_date) if f_name else (
                    generate_filename(None, f_mime, descname=f_descname, idx=f_idx, date=attach_date, relation_type=f_relation_type)
                )
                ok, msg = save_new_file(file_page, filename, fgd, client_id)
                if not ok:
                    return jsonify(msg, 500, 'ERROR')
                else:
                    db.session.commit()

            result = cviz.make_file_attach_info(cfa, False)
            return jsonify({
                'cfa': result
            })

    elif request.method == 'DELETE':
        data = request.args
        cfa_id = safe_int(data.get('cfa_id'))
        fm_id = safe_int(data.get('file_meta_id'))
        if cfa_id:
            delete_client_file_attach_and_relations(cfa_id)
            return jsonify(None)
        elif fm_id:
            fm = FileMeta.query.get(fm_id)
            fm.deleted = 1
            db.session.add(fm)
            FileMeta.query.filter(FileMeta.idx > fm.idx, FileMeta.deleted == 0).update({
                'idx': FileMeta.idx - 1
            })
            try:
                db.session.commit()
            except Exception, e:
                # todo:
                raise
            return jsonify(None)
        else:
            raise Exception

        return jsonify(None)