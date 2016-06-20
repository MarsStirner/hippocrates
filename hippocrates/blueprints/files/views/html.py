# -*- coding: utf-8 -*-

from flask import render_template, send_file

from ..app import module
from blueprints.files.lib.files import get_file_info, get_full_file_path


@module.route('/upload_form.html')
def html_upload_form():
    return render_template('files/upload_form.html')


@module.route('/<fileid>')
def serve_file(fileid):
    try:
        fileinfo = get_file_info(fileid)
        if not fileinfo:
            raise IOError
        return send_file(get_full_file_path(fileid), as_attachment=True, attachment_filename=fileinfo['name'])
    except IOError:
        return u'Файл не найден'