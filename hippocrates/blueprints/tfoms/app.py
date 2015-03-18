# -*- coding: utf-8 -*-
from .config import MODULE_NAME, RUS_NAME
from flask import Blueprint
from .utils import _config

module = Blueprint(MODULE_NAME, __name__, template_folder='templates', static_folder='static')


@module.context_processor
def module_name():
    return dict(module_name=RUS_NAME)


@module.context_processor
def menu_struct():
    m = [{'name': u'Главная',
          'url': '.index',
          },
         {'name': u'Выгрузка',
          'url': '.download',
          },
         {'name': u'Загрузка',
          'url': '.upload',
          },
         {'name': u'Отчеты',
          'url': '.reports',
          },
         {'name': u'Настройки',
          'subitems': [{'name': u'Шаблоны',
                        'url': '.add_new_template'},
                       {'name': u'Настройки модуля',
                        'url': '.settings'}],
          'restrict_access': True,
         }
         ]
    return dict(menu_struct=m)


from .views import *