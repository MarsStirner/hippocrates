# -*- coding: utf-8 -*-

from flask import request
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.admin.base import expose, BaseView
from wtforms.fields import SelectField, BooleanField

from blueprints.tfoms.models import *


class TemplateTypeView(ModelView):
    column_exclude_list = ('tags', )
    form_excluded_columns = ('tags', )
    column_labels = dict(code=u'Код', name=u'Наименование', download_type=u'Тип выгрузки')
    form_columns = ('code', 'name', 'download_type')
    column_list = ('code', 'name', 'download_type')

    def __init__(self, session, **kwargs):
        super(TemplateTypeView, self).__init__(TemplateType, session, **kwargs)


class TemplateView(ModelView):
    column_labels = dict(name=u'Наименование', type=u'Тип шаблона', archive=u'Архивировать')
    form_columns = ('name', 'type', 'archive')
    column_list = ('name', 'type', 'archive')

    def __init__(self, session, **kwargs):
        super(TemplateView, self).__init__(Template, session, **kwargs)


class StandartTreeView(ModelView):
    form_columns = ('template_type', 'parent', 'tag', 'ordernum', 'is_necessary')
    column_labels = dict(tag=u'Тэг',
                         parent=u'Родительский тэг',
                         template_type=u'Тип шаблона',
                         ordernum=u'Поле сортировки',
                         is_necessary=u'Обязательный')

    def __init__(self, session, **kwargs):
        super(StandartTreeView, self).__init__(StandartTree, session, **kwargs)


class TagsTreeView(ModelView):
    form_columns = ('template', 'parent', 'tag', 'ordernum')
    column_labels = dict(tag=u'Тэг',
                         parent=u'Родительский тэг',
                         ordernum=u'Поле сортировки',
                         template=u'Шаблон',)

    def __init__(self, session, **kwargs):
        super(TagsTreeView, self).__init__(TagsTree, session, **kwargs)