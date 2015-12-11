# -*- coding: utf-8 -*-
from flask import request
from sqlalchemy import func

from ..app import module
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_date
from nemesis.models.actions import TakenTissueJournal


@module.route('/api/get_ttj_records.json', methods=['GET'])
@api_method
def api_get_ttj_records():
    exec_date = safe_date(request.args.get('execDate'))
    ttj_records = TakenTissueJournal.query.filter(func.date(TakenTissueJournal.datetimeTaken) == exec_date).all()
    return ttj_records