# -*- encoding: utf-8 -*-
from flask import request

from application.lib.utils import jsonify
from application.systemwide import db
from ...app import module
from ...lib.represent import represent_checkup, get_action_by_id


@module.route('/api/0/checkup/', methods=['GET', 'POST'])
@module.route('/api/0/checkup/<int:checkup_id>', methods=['GET', 'POST'])
def api_0_checkup(checkup_id):
    if request.method == 'GET':
        action = get_action_by_id(checkup_id)
        if not action:
            return jsonify(None, 404, 'Action not found')
    else:
        action = get_action_by_id(checkup_id, True)
        for code, value in request.get_json().iteritems():
            if code not in ('id', 'flatCode', 'person', 'beg_date') and code in action.propsByCode:
                action.propsByCode[code].value = value
        db.session.commit()
    return jsonify(represent_checkup(action))