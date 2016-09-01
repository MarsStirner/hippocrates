#! coding:utf-8
"""


@author: BARS Group
@date: 14.04.2016

"""
from nemesis.lib.apiutils import ApiException

NOT_FOUND_ERROR = 404


class Schema(object):
    schema = None

    @classmethod
    def get_schema(cls, api_version):
        try:
            return cls.schema[api_version]
        except IndexError:
            raise ApiException(NOT_FOUND_ERROR, u'Версия API %i не поддерживается. Максимум %i' % (api_version, len(cls.schema) - 1))
