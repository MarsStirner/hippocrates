# -*- coding: utf-8 -*-

import logging
import traceback
from flask import g
from jinja2 import TemplateSyntaxError
from blueprints.print_subsystem.lib.internals import RenderTemplateException
from blueprints.print_subsystem.models.models_all import Rbprinttemplate
from internals import renderTemplate

__author__ = 'mmalkov'


# def printTeleMed(widget, clientInfo, eventInfo, context, act_context, data, actionsInfo, unloadingType, person):
#     templates = getPrintTemplates(context)
#     templatesInfo = templates
#     def tryApply(templateInfo):
#         try:
#             return applyTemplateNoPrint(templateInfo[1], data)
#         except:
#             return (u'', u'',
#                 CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5),
#                 {})
#     def tryApply_actions(index):
#         data['action'] = actionsInfo[index]
#         templatesInfo.extend(getPrintTemplates(act_context[index]))
#         return map(tryApply, getPrintTemplates(act_context[index]))
#
#     allRendered = map(tryApply, templates)
#     map(lambda index: allRendered.extend(tryApply_actions(index)), xrange(len(act_context)))
#     allHtml = u"\n<br style='page-break-after: always;'>\n".join(map(lambda item: item[0], allRendered))
#     allCanvases = {}
#     map(lambda item: allCanvases.update(item[3]), allRendered)
#
#     reportView = CReportViewDialog(widget)
#
#     reportView.setText(allHtml)
#     reportView.setCanvases(allCanvases)
#     reportView.setPageFormat(CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5))
#     #templatesInfo.extend(templates)
#     if unloadingType == u"TeleMed":
#         reportView.setWindowTitle(u"Телемедицинская консультация")
#         reportView.saveAsFile()
#     elif unloadingType == u"EMK":
#         reportView.setWindowTitle(u"Выгрузка в ЭМК")
#         reportView.saveAsTelemedFile(clientInfo, eventInfo, templatesInfo, person)


def applyTemplate(templateId, data):
    u"""Выводит на печать шаблон печати номер templateId с данными data"""
    template_data = g.printing_session.query(Rbprinttemplate).get(templateId)
    if not template_data:
        raise RenderTemplateException(u'Шаблон с id=%s не найден' % templateId, {
            'type': RenderTemplateException.Type.other,
            'template_name': '<unknown>',
            'trace': '',
        })
    try:
        return renderTemplate(template_data.templateText, data)
    except TemplateSyntaxError, e:
        print e
        logging.error('syntax error in template id = %s', templateId, exc_info=True)
        raise RenderTemplateException(e.message, {
            'type': RenderTemplateException.Type.syntax,
            'template_name': template_data.name,
            'lineno': e.lineno
        })
    except Exception, e:
        print unicode(traceback.format_exc(), 'utf-8')
        logging.critical('erroneous template id = %s', templateId, exc_info=True)
        tb = traceback.format_exc()
        if isinstance(tb, str):
            tb = tb.decode('utf-8')
        raise RenderTemplateException(e.message, {
            'type': RenderTemplateException.Type.other,
            'template_name': template_data.name,
            'trace': tb,
        })
