# coding: utf-8

from nemesis.lib.enum import EnumBase
from nemesis.lib.utils import safe_traverse
from nemesis.app import app


class SystemMode(EnumBase):
    """
    Режим работы приложения
    """
    normal = 1, u'Независимое приложение'
    sar_barsmis = 2, u'БАРС.МИС в Саратове'


class SpecificsManager(object):
    _app = None
    _system_mode = None

    @classmethod
    def init_from_app(cls, app):
        cls._app = app
        cls._system_mode = safe_traverse(
            app.config, 'system_prefs', 'mode', default=SystemMode.normal[0]
        )

    @classmethod
    def ext_card_url_menu_enabled(cls):
        return cls._system_mode in (SystemMode.sar_barsmis[0], )

    @classmethod
    def get_ext_card_url(cls, event):
        if not event:
            return '/'
        if cls._system_mode == SystemMode.sar_barsmis[0]:
            return get_sarbarsmis_card_url(event)

    @classmethod
    def get_ext_schedule_url(cls):
        return safe_traverse(app.config, 'system_prefs', 'integration', 'external_schedule_url', default='')

    @classmethod
    def get_ext_card_menu_text(cls):
        if cls._system_mode == SystemMode.sar_barsmis[0]:
            return u'История заболевания'

    @classmethod
    def get_reports_redirect_url(cls):
        if cls._system_mode == SystemMode.sar_barsmis[0]:
            return get_sarbarsmis_url()

    @classmethod
    def uses_regional_services(cls):
        return safe_traverse(
            app.config, 'system_prefs', 'regional', 'uses_regional_services', default=False
        )


def get_sarbarsmis_url():
    return safe_traverse(
        app.config, 'system_prefs', 'integration', 'BARS_MIS_URL', default=''
    ).rstrip('/')


def get_sarbarsmis_card_url(event):
    ext_url = get_sarbarsmis_url()
    if not ext_url:
        return None
    ext_id = event.client_id
    return u'{0}/ws/cas_risar?page=DISEASECASE&form=1&risar_id={1}'.format(ext_url, ext_id)


def get_service_table_name():
    return 'rbService_regional' if SpecificsManager.uses_regional_services() else 'SST365'
