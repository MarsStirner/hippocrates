# -*- encoding: utf-8 -*-

from hippocrates.blueprints.risar.app import module
from hippocrates.blueprints.risar.lib.represent import represent_concilium
from hippocrates.blueprints.risar.lib.concilium import get_concilium_list, get_concilium_by_id
from nemesis.lib.apiutils import api_method, ApiException
from nemesis.models.event import Event


@module.route('/api/0/pregnancy/chart/<int:event_id>concilium/list')
@api_method
def api_0_concilium_list_get(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    concilium_list = get_concilium_list(event_id)
    return [
        represent_concilium(concilium)
        for concilium in concilium_list
    ]


@module.route('/api/0/pregnancy/chart/<int:event_id>concilium/')
@module.route('/api/0/pregnancy/chart/<int:event_id>concilium/<int:concilium_id>')
@api_method
def api_0_concilium_get(event_id, concilium_id=None):
    event = Event.query.get(event_id)
    if not event:
        raise ApiException(404, u'Обращение не найдено')
    concilium = get_concilium_by_id(concilium_id)
    return represent_concilium(concilium)