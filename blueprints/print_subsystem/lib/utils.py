# -*- coding: utf-8 -*-
# from PyQt4 import QtGui, QtCore
import codecs
import logging
import os
# import sip
# from library.Journaling import CJournaling
# from library.TextDocument import CTextDocument
# from library.Utils import forceString, forceInt, forceRef
# from internals import renderTemplate, CPageFormat
#from specialvars import getSpVarsUsedInTempl, getSpecialVariableValue, SpecialVariable
from flask import g
from ..models.models_all import Rbprinttemplate

__author__ = 'mmalkov'


def getPrintTemplates(context):
    return [
        (r.name, r.id, r.dpdAgreement, r.fileName, r.code)
        for r in g.printing_session.query(Rbprinttemplate).filter(Rbprinttemplate.context == context)
    ] if context else []

