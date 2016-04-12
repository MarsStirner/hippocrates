# -*- coding: utf-8 -*-
import collections

import requests
from flask import request
from nemesis.app import app
from nemesis.lib.settings import Settings
from sqlalchemy import func

from ..app import module
from ..lib.utils import TTJVisualizer
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_date
from nemesis.models.actions import TakenTissueJournal, Action_TakenTissueJournalAssoc
from nemesis.models.enums import TTJStatus
from nemesis.systemwide import db


@module.route('/api/get_ttj_records.json', methods=['POST'])
@api_method
def api_get_ttj_records():
    vis = TTJVisualizer()
    data = request.json
    number_by_status = {'all': 0, 'waiting': 0, 'in_progress': 0, 'sending_to_lab': 0, 'finished': 0}

    flt = data.get('filter')

    status = flt.get('status')
    exec_date = safe_date(flt.get('execDate'))
    biomaterial = flt.get('biomaterial')
    lab = flt.get('lab')
    org_str = flt.get('org_struct')

    test_tubes = collections.defaultdict(lambda: {'number': 0})
    query = TakenTissueJournal.query.filter(func.date(TakenTissueJournal.datetimeTaken) == exec_date)
    if status is not None:
        query = query.filter(TakenTissueJournal.statusCode == status)
    if biomaterial:
        query = query.filter(TakenTissueJournal.tissueType_id == biomaterial['id'])
    ttj_records = query.all()
    number_by_status['all'] = len(ttj_records)

    def filter_by_lab(ttj_record):
        for action in ttj_record.actions:
            for property in action.properties:
                lab_codes = [item.laboratory.code for item in property.type.test.lab_test] if property.type.test else []
                if property.isAssigned and lab['code'] in lab_codes:
                    return True

    def filter_by_org_str(ttj_record):
        if ttj_record.actions[0].event.current_org_structure.code == org_str['code']:
            return True

    if lab:
        ttj_records = filter(filter_by_lab, ttj_records)
    if org_str:
        ttj_records = filter(filter_by_org_str, ttj_records)

    def count_tubes(x, y):
        x[y.testTubeType.code]['name'] = y.testTubeType.name
        x[y.testTubeType.code]['number'] += len(y.actions)
        number_by_status[TTJStatus.codes[y.status.value]] += 1
        return x

    reduce(count_tubes, ttj_records, test_tubes)
    return {'ttj_records': [vis.make_ttj_record(record) for record in ttj_records],
            'test_tubes': test_tubes,
            'number_by_status': number_by_status}


@module.route('/api/ttj_change_status.json', methods=['POST'])
@api_method
def api_ttj_change_status():
    result = None
    data = request.json
    status = data.get('status')
    ids = data.get('ids')
    if not status:
        raise ApiException(400, u'Invalid request. `status` must be set')
    if not ids:
        raise ApiException(400, u'Invalid request. `ids` must be non-empty list')
    core_integration_address = Settings.getString('appPrefs.CoreWS.LIS-1022')
    if status['code'] == 'finished' and core_integration_address:
        auth_token_cookie = app.config.get('CASTIEL_AUTH_TOKEN')
        sess = requests.session()
        sess.cookies[auth_token_cookie] = request.cookies[auth_token_cookie]
        aids = set(
            assoc.action_id
            for assoc in Action_TakenTissueJournalAssoc.query.filter(
               Action_TakenTissueJournalAssoc.takenTissueJournal_id.in_(ids)
            )
        )
        try:
            result = sess.put(
                core_integration_address,
                json={'ids': list(aids)}
            )
        except requests.ConnectionError:
            raise ApiException(500, u'Cannot connect to core')
    TakenTissueJournal.query.filter(
        TakenTissueJournal.id.in_(ids)
    ).update(
        {TakenTissueJournal.statusCode: status['id']},
        synchronize_session=False
    )
    db.session.commit()
    return result
