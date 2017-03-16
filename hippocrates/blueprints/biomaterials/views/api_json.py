# -*- coding: utf-8 -*-
import collections
import datetime

import blinker as blinker

import requests
from flask import request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from nemesis.app import app
from nemesis.lib.settings import Settings
from nemesis.models.event import Event
from nemesis.models.exists import rbLaboratory, rbTest, rbLaboratory_TestAssoc, rbTestTubeType
from nemesis.models.utils import safe_current_user_id

from ..app import module
from ..lib.utils import TTJVisualizer
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.lib.utils import safe_date, bail_out, safe_traverse
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from nemesis.models.actions import TakenTissueJournal, Action_TakenTissueJournalAssoc, Action, ActionPropertyType, \
    ActionProperty
from nemesis.models.enums import TTJStatus
from nemesis.systemwide import db
from nemesis.lib.mq_integration.biomaterial import notify_biomaterials_changed, MQOpsBiomaterial


@module.route('/api/get_ttj_records.json', methods=['POST'])
@api_method
def api_get_ttj_records():
    vis = TTJVisualizer()
    data = request.json
    flt = data.get('filter')

    barcode = flt.get('barCode')
    min_barcode_len = safe_traverse(app.config, 'system_prefs', 'ui', 'ttj_barcode_len')
    search_by_barcode = min_barcode_len is not None and barcode
    exec_date = safe_date(flt.get('execDate'))
    biomaterial = flt.get('biomaterial')
    lab = flt.get('lab')
    org_str = flt.get('org_struct')

    result = {}

    query = TakenTissueJournal.query.join(
        Event, rbTestTubeType, Action_TakenTissueJournalAssoc, Action, ActionProperty, ActionPropertyType, rbTest,
        rbLaboratory_TestAssoc, rbLaboratory
    ).filter(
        Action.deleted == 0,
        ActionProperty.isAssigned == 1,
    )

    if search_by_barcode:
        if len(barcode) < min_barcode_len:
            return result
        query = query.filter(func.concat(TakenTissueJournal.period, TakenTissueJournal.barcode).like(u'{0}%'.format(barcode)))
    else:
        query = query.filter(func.date(TakenTissueJournal.datetimePlanned) == exec_date)

        if biomaterial:
            query = query.filter(TakenTissueJournal.tissueType_id == biomaterial['id'])

    query = query.options(
        joinedload(TakenTissueJournal.tissueType),
    ).with_entities(
        TakenTissueJournal.id,
        TakenTissueJournal,
        Action,
        rbLaboratory,
        Event,
        rbTestTubeType,
    )

    filtered = query.all()

    if not search_by_barcode:
        if org_str:
            filtered = [
                record for record in filtered
                if record.Event.current_org_structure and record.Event.current_org_structure.id == org_str['id']
            ]
        if lab:
            filtered = [
                record for record in filtered
                if record.rbLaboratory.id == lab['id']
            ]

    def make_default_result_record(record):
        return {
            'ttj': record.TakenTissueJournal,
            'actions': {record.Action},
            'labs': {record.rbLaboratory},
            'ttt': {record.rbTestTubeType},
        }

    mapping = {}
    all_action_ids = set()
    for record in filtered:
        if record[0] not in mapping:
            r = mapping[record[0]] = make_default_result_record(record)
        else:
            r = mapping[record[0]]
        r['actions'].add(record.Action)
        all_action_ids.add(record.Action.id)
        r['labs'].add(record.rbLaboratory)
        r['ttt'].add(record.rbTestTubeType)

    all_records = mapping.values()
    all_records.sort(key=lambda x: x['ttj'].datetimePlanned)

    s_ctrl = ServiceController()
    pay_data = s_ctrl.get_actions_pay_info(all_action_ids)

    ttj_by_status = {
        ttj_status_code: [
            record
            for record in all_records 
            if record['ttj'].status.value == ttj_value
        ]
        for ttj_value, ttj_status_code in TTJStatus.codes.items()
    }

    for ttj_status, records in ttj_by_status.iteritems():
        tube_dict = collections.defaultdict(lambda: {'name': None, 'count': 0})
        for record in records:
            for ttt in record['ttt']:
                tube_dict[ttt.code]['name'] = ttt.name
                tube_dict[ttt.code]['count'] += len(record['actions'])

        ttj_records = []
        for record in records:
            pays = dict((a.id, pay_data.get(a.id)) for a in record['actions'])
            ttj_records.append(
                vis.make_ttj_record(record['ttj'], record['actions'], pays)
            )

        result[ttj_status] = {
            'records': ttj_records,
            'tubes': tube_dict,
        }
    return result


def core_notify_takentissuejournal(sender, ids):
    core_integration_address = Settings.getString('appPrefs.CoreWS.LIS-1022')
    if not core_integration_address or not ids:
        return

    auth_token_cookie = app.config.get('CASTIEL_AUTH_TOKEN')
    sess = requests.session()
    sess.cookies[auth_token_cookie] = request.cookies[auth_token_cookie]
    try:
        sess.put(
            core_integration_address,
            json={'ids': list(ids)},
            timeout=10,
        )
    except requests.ConnectionError:
        raise ApiException(500, u'Не удалось связаться с ядром')

blinker.signal('Core.Notify.TakenTissueJournal').connect(core_notify_takentissuejournal)


@module.route('/api/ttj_change_status.json', methods=['POST'])
@api_method
def api_ttj_change_status():
    data = request.json
    status = data.get('status') or bail_out(ApiException(400, u'Invalid request. `status` must be set'))
    ids = data.get('ids') or bail_out(ApiException(400, u'Invalid request. `ids` must be non-empty list'))
    if status['code'] in ['sent_to_lab', 'fail_to_lab']:
        raise ApiException(403, u'Только внешняя система имеет право устанавливать этот статус: %s' % status['code'])
    if status['code'] not in ['waiting', 'in_progress', 'finished']:
        raise ApiException(400, u'Неизвестный код: %s' % status['code'])
    rule = {TakenTissueJournal.statusCode: status['id']}
    if status['code'] == 'finished':
        rule[TakenTissueJournal.execPerson_id] = safe_current_user_id()
        rule[TakenTissueJournal.datetimeTaken] = datetime.datetime.now()
    TakenTissueJournal.query.filter(
        TakenTissueJournal.statusCode < TTJStatus.finished[0],  # Не менять статусы уже законченных
        TakenTissueJournal.id.in_(ids),
    ).update(rule, synchronize_session=False)
    db.session.commit()
    if status['code'] == 'finished':
        blinker.signal('Core.Notify.TakenTissueJournal').send(None, ids=ids)
        notify_biomaterials_changed(MQOpsBiomaterial.send, ids)
