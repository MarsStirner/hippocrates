# -*- coding: utf-8 -*-
import collections

from flask import request
from sqlalchemy import func

from ..app import module
from ..lib.utils import TTJVisualizer
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_date
from nemesis.models.actions import TakenTissueJournal
from nemesis.models.enums import TTJStatus
from nemesis.systemwide import db


@module.route('/api/get_ttj_records.json', methods=['POST'])
@api_method
def api_get_ttj_records():
    vis = TTJVisualizer()
    data = request.json
    number_by_status = {'all': 0, 'waiting': 0, 'in_progress': 0, 'sending_to_lab': 0, 'finished': 0}

    filter = data.get('filter')

    status = filter.get('status')
    exec_date = safe_date(filter.get('execDate'))
    biomaterial = filter.get('biomaterial')

    test_tubes = collections.defaultdict(lambda: {'number': 0})
    query = TakenTissueJournal.query.filter(func.date(TakenTissueJournal.datetimeTaken) == exec_date)
    if status is not None:
        query = query.filter(TakenTissueJournal.statusCode == status)
    if biomaterial:
        query = query.filter(TakenTissueJournal.tissueType_id == biomaterial['id'])
    ttj_records = query.all()
    number_by_status['all'] = len(ttj_records)

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
    data = request.json
    status = data.get('status')
    ids = data.get('ids')
    TakenTissueJournal.query.filter(TakenTissueJournal.id.in_(ids),).update({'status': status['id']},
                                                                            synchronize_session=False)
    db.session.commit()