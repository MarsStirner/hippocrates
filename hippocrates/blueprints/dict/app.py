# -*- coding: utf-8 -*-
from flask import Blueprint
from .utils import _config
from .config import MODULE_NAME, RUS_NAME

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(module_name=RUS_NAME)


@module.context_processor
def menu_struct():
    m = [{'name': u'Главная',
          'url': '.index',
          },
         {'name': u'Тарифы',
          'subitems': [{'name': u'Загрузка',
                        'url': '.tariff_upload'}]
          },
         {'name': u'Настройки',
          'url': '.settings',
          'restrict_access': True,
          }
         ]
    return dict(menu_struct=m)


from .views import *
from .views.tariff import *