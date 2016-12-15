#! coding:utf-8
"""


@author: BARS Group
@date: 10.05.2016

Description:
https://conf.bars-open.ru/pages/viewpage.action?pageId=27505440

Usage:
jasper_client = JasperReport(
    'SearchPrint',
    '/reports/Custom/SearchPrint',
    fields=('name', 'risk', 'curators', 'week')
)
file_format = 'pdf'
data = [{'name': 'name', 'risk': 'risk', 'curators': 'curators', 'week': 'week'}]
jasper_client.generate(file_format, data)
jasper_client.save_to_file('/var/tmp/')
flask.make_response(jasper_report.get_response_data())

"""

import os
import uuid
import requests
from nemesis.systemwide import db
from nemesis.app import app


def get_mime_type(file_format, open_type=None):
    open_type = open_type or 'attachment'
    if file_format == 'pdf':
        return '%s/pdf' % open_type
    elif file_format == 'docx':
        return '%s/vnd.openxmlfile_formats-officedocument.wordprocessingml.document' % open_type
    elif file_format == 'xlsx':
        return '%s/vnd.openxmlfile_formats-officedocument.spreadsheetml.sheet' % open_type
    elif file_format == 'odt':
        return '%s/vnd.oasis.opendocument.text' % open_type
    elif file_format == 'rtf':
        return '%s/rtf' % open_type
    elif file_format == 'xls':
        return '%s/vnd.ms-excel' % open_type
    elif file_format == 'html':
        return 'text/html'
    else:
        return '%s/pdf' % open_type


class JasperDBMemoryDataSource(object):
    """
    Place python data to memory DB table for jasper report
    """
    def __init__(self, table_name, fields):
        self.fields = fields
        self.uid = str(uuid.uuid4())
        self.full_table_name = '`JasperReport_%(table_name)s_%(uid)s`' % ({
            'table_name': table_name,
            'uid': self.uid,
        })

    def create_report_table(self):
        create_query = '''
        CREATE TABLE IF NOT EXISTS %(table_name)s (%(columns)s)
        COLLATE='utf8_general_ci'
        ENGINE=MEMORY
        ;
        ''' % ({
            'table_name': self.full_table_name,
            'columns': ', '.join((
                x.join(['`', '`']) + ' VARCHAR(50) NULL' for x in self.fields
            )),
        })
        db.session.execute(create_query)

    def delete_report_table(self):
        drop_query = '''
        DROP TABLE IF EXISTS %(table_name)s;
        ''' % ({'table_name': self.full_table_name})
        db.session.execute(drop_query)

    def fill_report_table(self, data):
        insert_query = '''
        INSERT INTO %(table_name)s (%(columns)s) VALUES (%(values)s)
        '''
        for r in data:
            keys, vals = zip(*r.items())
            db.session.execute(
                insert_query % ({
                    'table_name': self.full_table_name,
                    'columns': ', '.join(keys),
                    'values': ', '.join((
                        unicode(x is not None and x or '').join(('"', '"'))
                        for x in vals
                    )),
                }))

    def get_request_params(self):
        return {
            'table_name': self.full_table_name,
            'uid': self.uid,
        }


class JasperRestV2Client(object):
    """
    Client of JasperReports server
    """
    def __init__(self, path=None, session=None, params=None):
        self.path = path
        self.session = session
        self.jasper_url = app.config.get(
            'JASPER_URL', 'http://10.1.2.11:8080/jasperserver-pro'
        )
        self.jasper_lg = app.config.get('JASPER_LOGIN', 'jasperadmin')
        self.jasper_pw = app.config.get('JASPER_PASSWORD', 'jasperadmin')
        self._params = params
        self._cookies = None

    def jasper_login(self):
        if not self.session:
            res = self.api_request(
                'post', '/rest/login',
                data={'j_username': self.jasper_lg,
                      'j_password': self.jasper_pw},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            # todo: доставать path из cookies
            self.session = res.cookies.get('JSESSIONID'), '/jasperserver-pro/', '0'

        session_id, path, version = self.session
        self._cookies = {
            'JSESSIONID': session_id,
            '$Path': path,
            '$Version': version,
        }

    def running_report(self, res_format):
        assert self.path
        self.jasper_login()

        url = '/rest_v2/reports%(path)s.%(format)s' % ({
            'path': self.path,
            'format': res_format,
        })
        result = self.api_request(
            'get', url,
            params=self._params,
            cookies=self._cookies,
        )
        return result.content

    def searching_repository(self):
        self.jasper_login()

        url = '/rest_v2/resources'
        result = self.api_request(
            'get', url,
            params=self._params,
            cookies=self._cookies,
            headers={'accept': 'application/json'},
        )
        return result.json()['resourceLookup']

    def api_request(self, method, url, **kwargs):
        result = getattr(requests, method)(self.jasper_url + url, **kwargs)
        if result.status_code != 200:
            message = unicode(result.text)
            raise Exception(
                unicode(u'Api Error: {0}'.format(message)).encode('utf-8')
            )
        return result


class JasperReport(object):
    """
    Generate report
    """
    def __init__(self, table_name, path, params=None, fields=None, session=None):
        """
        :param table_name: Наименование результирующего файла отчета, а так же временной таблицы в БД
        :param path: Путь к шаблону отчета в репозитории JasperReports
        :param params: Словарь параметров отчета
        :param fields: Список наименований полей шаблона
        :param session: Сессия доступа к серверу JasperReports
        """
        self.table_name = table_name
        if fields is None:
            self.dsource = None
        else:
            self.dsource = JasperDBMemoryDataSource(table_name, fields)
            params = params or {}
            params.update(self.dsource.get_request_params())
        params.update(self.mongo_params)
        self.jclient = JasperRestV2Client(path, session, params)

    @property
    def mongo_params(self):
        return {
            'mongo_host': app.config.get('MONGO_HOST', '10.1.2.11'),
            'mongo_port': app.config.get('MONGO_PORT', '27017'),
            'mongo_dbname': app.config.get('MONGO_DBNAME', 'nvesta'),
            'mongo_user': app.config.get('MONGO_USERNAME', ''),
            'mongo_pw': app.config.get('MONGO_PASSWORD', ''),
        }

    def generate(self, file_format, data=None):
        """
        Генерация отчета
        :param file_format: Формат файла отчета
        :param data: Данные для отчета, передаваемые из веб приложения
        :return: Содержимое файла отчета
        """
        self.report = None
        self.file_format = file_format
        if data is None:
            self.report = self.jclient.running_report(file_format)
        else:
            self.dsource.create_report_table()
            try:
                self.dsource.fill_report_table(data)
                self.report = self.jclient.running_report(file_format)
            finally:
                self.dsource.delete_report_table()
        return self.report

    def save_to_file(self, file_place):
        """
        Сохранение отчета на диск
        :param file_place: путь к файлу
        """
        with open('.'.join(
            (os.path.join(file_place, self.table_name), self.file_format)
        ), 'wb') as f:
            f.write(self.report)

    def get_response_data(self, open_type=None):
        """
        Возврат отчета браузеру для доступа к отчету пользователем
        :return: Данные ответа браузеру
        """
        return self.report, 200, {
            'Content-Type': get_mime_type(self.file_format, open_type),
            'Content-Disposition': 'inline; filename="%s.%s"' % (
                self.table_name, self.file_format
            ),
        }

    @property
    def session(self):
        """
        Сессия доступа к серверу отчетов, чтобы не выполнять повторный вход
        :return: Данные сессии
        """
        return self.jclient.session

    @classmethod
    def get_reports(cls, locate_reports):
        params = {
            'folderUri': locate_reports,
            'type': 'reportUnit',
            'sortBy': 'description',
        }
        jclient = JasperRestV2Client(params=params)
        return jclient.searching_repository()

    @classmethod
    def multi_generating(cls, report_data_list):
        # если станет нужно для нескольких отчетов на один запрос
        session = None
        response = []
        for report_data in report_data_list:
            template_uri, template_code, params = report_data
            table_name, file_format = template_code.rsplit('.', 1)
            jasper_report = cls(
                table_name,
                template_uri,
                params=params,
                session=session,
            )
            jasper_report.generate(file_format)
            response.append(jasper_report.get_response_data())
            session = jasper_report.session
        return response
