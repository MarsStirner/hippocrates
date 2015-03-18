# -*- coding: utf-8 -*-

from flask import abort, request

from application.systemwide import db
from application.lib.utils import jsonify, logger, parse_id, public_endpoint, safe_int
from blueprints.patients.app import module
from application.lib.sphinx_search import SearchPatient
from application.lib.jsonify import ClientVisualizer
from application.models.client import Client, ClientFileAttach
from application.models.exists import FileMeta, FileGroupDocument
from blueprints.patients.lib.utils import *


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
    from application.models.kladr_models import Kladr
    val = request.args['city']
    res = Kladr.query.filter(Kladr.NAME.startswith(val)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])


@module.route('/api/kladr_street.json', methods=['GET'])
def api_kladr_street_get():
    from application.models.kladr_models import Street
    city = request.args['city']
    street = request.args['street']
    res = Street.query.filter(Street.CODE.startswith(city[:-2]), Street.NAME.startswith(street)).all()
    return jsonify([{'name': r.NAME,
                    'code': r.CODE} for r in res])


import base64
import datetime
import os
import mimetypes
from application.app import app
from sqlalchemy import func


def get_file_ext_from_mimetype(mime):
    if not mime:
        return ''
    ext_list = mimetypes.guess_all_extensions(mime)
    ext = ''
    if ext_list:
        if len(ext_list) == 1:
            ext = ext_list[0]
        elif '.xls' in ext_list:
            ext = '.xls'
    return ext


def generate_filename(name, mime, descname=None, idx=None, date=None, relation_type=None):
    file_ext = get_file_ext_from_mimetype(mime)
    if name:
        filename = u"{0}_{1:%y%m%d_%H%M}{2}".format(name, date, file_ext)
    else:
        template = u'{descname}_{reltype}Лист_№{idx}_{date:%y%m%d_%H%M}{ext}'
        date = date or datetime.datetime.now()
        filename = template.format(
            descname=descname, idx=idx, date=date,
            reltype=u'({0})_'.format(relation_type) if relation_type else u'',
            ext=file_ext
        )
    return filename


def store_file_locally(filepath, file_data):
    uri_string = file_data
    data_string = uri_string.split(',')[1]  # seems legit
    data_string = base64.b64decode(data_string)
    dirname = os.path.dirname(filepath)
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(data_string)
    except IOError, e:
        logger.error(u'Ошибка сохранения файла средствами МИС: %s' % e, exc_info=True)
        return False, u'Ошибка сохранения файла'
    # TODO: manage exceptions
    return True, ''


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

            cfa_query_result = ClientFileAttach.query.join(FileGroupDocument, FileMeta).filter(
                ClientFileAttach.id == cfa_id,
                FileMeta.idx == idx
            ).first()
            cfa = cviz.make_file_attach_info(cfa_query_result, True, [idx]) if cfa_query_result else None
            other_file_pages = db.session.query(
                FileMeta.id, FileMeta.idx
            ).select_from(ClientFileAttach).join(
                FileGroupDocument, FileMeta
            ).filter(
                ClientFileAttach.id == cfa_id
            ).all()

            return jsonify({
                'cfa': cfa,
                'other_pages': other_file_pages
            })

    elif request.method == 'POST':
        data = request.json
        client_id = safe_int(data.get('client_id'))
        file_attach = data.get('file_attach')
        if not file_attach:
            raise Exception
        cfa_id = file_attach.get('id')

        if cfa_id:
            pass
        else:
            attach_date = file_attach.get('attach_date') or datetime.datetime.now()
            doc_type = file_attach.get('doc_type')
            relation_type = file_attach.get('relation_type')

            file_document = file_attach.get('file_document')
            document_name = file_document.get('name')
            files_pages = file_document.get('files')

            fgd = FileGroupDocument()
            fgd.name = document_name
            cfa = ClientFileAttach()
            cfa.client_id = client_id
            cfa.attachDate = attach_date
            cfa.documentType_id = safe_traverse(doc_type, 'id')
            cfa.relationType_id = safe_traverse(relation_type, 'id')
            cfa.file_document = fgd
            db.session.add(fgd)
            db.session.add(cfa)
            try:
                db.session.commit()
            except Exception, e:
                # todo:
                raise

            new_file_list = []
            f_descname = safe_traverse(doc_type, 'name', default=u'Файл')
            f_relation_type = safe_traverse(relation_type, 'leftName', default=u'')
            for file_page in files_pages:
                f_meta = file_page.get('meta')
                f_file = file_page.get('file')
                f_name = f_meta.get('name')
                f_idx = f_meta.get('idx')
                f_mime = f_file.get('mime')

                filename = generate_filename(f_name, f_mime, date=attach_date) if f_name else (
                    generate_filename(None, f_mime, descname=f_descname, idx=f_idx, date=attach_date, relation_type=f_relation_type)
                )

                fm = FileMeta()
                fm.name = filename
                fm.filegroup = fgd  # не очень оптимальная связка, появляется селект
                fm.idx = f_idx
                fm.deleted = 1
                try:
                    db.session.commit()
                except Exception, e:
                    # todo:
                    raise
                else:
                    new_file_list.append(fm)

                # При интеграции с ЗХПД
                # if config.secure_person_data_storage_enabled:
                #     store_in_external_system()
                #     ...

                # TODO: при сохранении файлов для другой связанной сущности изменить префикс директории
                directory = 'c%s' % client_id
                filepath = os.path.join(directory, filename)
                fullpath = os.path.join(app.config['FILE_STORAGE_PATH'], filepath)
                ok, msg = store_file_locally(fullpath, f_file.get('data'))
                if not ok:
                    return jsonify(msg, 500, 'ERROR')
                else:
                    fm.query.filter(FileMeta.id == fm.id).update({
                        'deleted': 0,
                        'path': filepath
                    })
        return jsonify(None)

    elif request.method == 'DELETE':
        return