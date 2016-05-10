#! coding:utf-8
"""


@author: BARS Group
@date: 10.05.2016

Usage:
jasper_client = JasperReport(
    'SearchPrint',
    ('name', 'external_id', 'exec_person_name', 'risk', 'curators', 'week'),
    '/reports/Custom/SearchPrint'
)
jasper_client.generate(data, file_format)
jasper_client.save_to_file('/var/tmp/')
flask.make_response(jasper_report.get_response_data())
"""
import os
import uuid
import requests
from nemesis.systemwide import db


def get_mime_type(file_format, open_type='attachment'):
    # open_type = 'application'
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
    else:
        return '%s/pdf' % open_type


class JasperDBMemoryDataSource(object):
    """
    Place python data to memory DB table for jasper report
    """
    def __init__(self, table_name, fields):
        self.fields = fields
        self.uid = str(uuid.uuid4())
        self.full_table_name = '`JasperReport%(table_name)s_%(uid)s`' % ({
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


class JasperRest2Client(object):
    def __init__(self, path, session=None, params=None):
        self.path = path
        self.session = session
        self.jasper_url = os.getenv('JASPER_URL', 'http://10.1.2.11:8080/jasperserver-pro')
        self.jasper_lg = os.getenv('JASPER_LOGIN') or 'jasperadmin'
        self.jasper_pw = os.getenv('JASPER_PASSWORD') or 'jasperadmin'
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
        self.jasper_login()

        url = u'/rest_v2/reports%(path)s.%(format)s' % ({
            'path': self.path,
            'format': res_format,
        })
        result = self.api_request(
            'get', url,
            params=self._params,
            cookies=self._cookies,
        )
        return result.content

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
    Generate report by python created data
    """
    def __init__(self, table_name, fields, path, session=None):
        self.table_name = table_name
        self.dsource = JasperDBMemoryDataSource(table_name, fields)
        params = self.dsource.get_request_params()
        self.jclient = JasperRest2Client(path, session, params)

    def generate(self, data, file_format):
        self.report = None
        self.file_format = file_format
        self.dsource.create_report_table()
        try:
            self.dsource.fill_report_table(data)
            self.report = self.jclient.running_report(file_format)
        finally:
            self.dsource.delete_report_table()
        return self.report

    def save_to_file(self, file_place):
        with open('.'.join(
            (os.path.join(file_place, self.table_name), self.file_format)
        ), 'wb') as f:
            f.write(self.report)

    def get_response_data(self):
        return self.report, 200, {
            'Content-Type': get_mime_type(self.file_format),
            'Content-Disposition': 'inline; filename="%s.%s"' % (
                self.table_name, self.file_format
            ),
        }
