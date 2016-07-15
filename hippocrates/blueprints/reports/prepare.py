#! coding:utf-8
"""


@author: BARS Group
@date: 13.05.2016

"""

import datetime

from hippocrates.blueprints.reports.models import rbRisarPrintTemplateMeta
from nemesis.lib.utils import string_to_datetime


class InputPrepare(object):
    def __init__(self):
        self.today = datetime.date.today()

    def update_context(self, template_uri, context):
        # подготовка типов данных в нужном виде для отчетов jasperreports
        for desc in rbRisarPrintTemplateMeta.query.filter(rbRisarPrintTemplateMeta.template_uri == template_uri):
            name = desc.name
            if name not in context:
                continue
            value = context[name]
            typeName = desc.type
            # if typeName == 'Integer':
            #     context[name] = int(value)
            # elif typeName == 'Float':
            #     context[name] = float(value)
            # elif typeName == 'Boolean':
            #     context[name] = bool(value)
            if typeName == 'Date':
                context[name] = string_to_datetime(value).date() if value else None
            elif typeName == 'Time':
                context[name] = datetime.datetime.strptime(value, '%H:%M').time() if value else None
            elif typeName in ('MultiRefBook', 'MultiOrganisation', 'MultiOrgStructure',
                              'MultiPerson', 'MultiService', 'MultiMKB',):
                context[name] = ','.join((str(x['id']) for x in value)) if value else None
            elif typeName in ('MultiArea',):
                context[name] = ','.join((str(x['code']) for x in value)) if value else None
            # elif typeName == 'Organisation':
            #     context[name] = Organisation.query.get(int(value)) if value else None
            # elif typeName == 'Person':
            #     context[name] = Person.query.get(int(value)) if value else None
            # elif typeName == 'OrgStructure':
            #     context[name] = OrgStructure.query.get(int(value)) if value else None
            # elif typeName == 'Service':
            #     context[name] = rbService.query.get(int(value)) if value else None
            # elif typeName == 'MKB':
            #     context[name] = MKB.query.get(int(value)) if value else None
            if not context[name]:
                context[name] = ''

    def report_data(self, doc):
        context_type = doc['context_type']
        template_id = doc['id']
        template_code = doc['code']
        data = self.get_context(context_type, doc)
        return template_id, template_code, data

    def get_context(self, context_type, data):
        context = dict(data['context'])
        self.update_context(data['id'], context)
        # if 'special_variables' in context:
        #     # Я надеюсь, что нам не придётся этим пользоваться
        #     ext = {}
        #     for sp_name in context['special_variables']:
        #         ext[sp_name] = SpecialVariable(sp_name, **context)
        #     del context['special_variables']
        #     context.update(ext)
        # context.update({
        #     'SpecialVariable': SpecialVariable
        # })

        context_func = getattr(self, 'context_%s' % context_type, None)
        if context_func and callable(context_func):
            context.update(context_func(context))
        return context
