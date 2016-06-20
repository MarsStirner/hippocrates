# -*- coding: utf-8 -*-

import itertools
import logging

from flask import request, make_response, abort

from blueprints.files.app import module
from blueprints.files.lib.files import (save_new_file, save_file_attach, get_file_meta_list,
    represent_file_meta, get_file_info)
from nemesis.lib.apiutils import api_method, ApiException, RawApiResult
from nemesis.lib.utils import parse_json


logger = logging.getLogger('simple')


@module.route('/api/0/upload', methods=['POST'])
@api_method
def api_0_upload():
    # files in form data
    files = request.files.getlist('files')
    if not files:
        raise ApiException(400, u'Нет файлов для загрузки')

    # additional info can be in form data separate fields
    # file_names = request.form.getlist('file[name]')
    # file_notes = request.form.getlist('file[note]')

    # and additional info can be inf form data `info` json string
    info = parse_json(request.form.get('info')) or {}
    files_info = info.get('files_info') or []
    attach_data = info.get('attach_data')

    errors = []
    metas = []
    for file, file_info in itertools.izip_longest(files, files_info):
        try:
            fmeta = save_new_file(file, file_info)
        except Exception, e:
            logger.exception(u'Ошибка сохранения файла {0}'.format(file.filename))
            errors.append({
                'info': file_info,
                'exc_message': unicode(e)
            })
        else:
            if attach_data is not None:
                save_file_attach(fmeta, attach_data)
            metas.append(fmeta)
    return {
        'files': [
            represent_file_meta(fmeta)
            for fmeta in metas
        ],
        'errors': errors
    }


@module.route('/api/0/file_list', methods=['GET'])
@api_method
def api_0_file_list_get():
    fmetas = get_file_meta_list()
    return {
        'files': fmetas
    }


@module.route('/api/0/download/<fileid>', methods=['GET'])
@api_method
def api_0_file_download(fileid):
    fileinfo = get_file_info(fileid)
    if not fileinfo:
        raise ApiException(404, u'Файл не найден')

    headers = {
        'Content-Description': 'File Transfer',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/octet-stream',
        # 'Content-Length': file_size,
        'Content-Disposition': u'attachment; filename={0}'.format(fileinfo['name']).encode('utf-8'),
        # nginx: http://wiki.nginx.org/NginxXSendfile
        'X-Accel-Redirect': u'/protected_files/{0}'.format(fileinfo['path']).encode('utf-8')
    }
    res = RawApiResult(None, extra_headers=headers)
    return res
