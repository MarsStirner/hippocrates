# -*- encoding: utf-8 -*-
import os
import errno
import exceptions
from datetime import date, datetime, timedelta
from zipfile import ZipFile, ZIP_DEFLATED
import dbf
from flask import current_app
from jinja2 import Environment, PackageLoader
from application.systemwide import db
from service_client import TFOMSClient as Client
from thrift_service.ttypes import InvalidArgumentException, NotFoundException, SQLException, TException
from thrift_service.ttypes import PatientOptionalFields, SluchOptionalFields, TClientPolicy, Payment
from thrift_service.ttypes import PersonOptionalFields
from ..app import module, _config
from ..models import Template, TagsTree, Tag
from ..lib.reports import Reports

try:
    from lxml import etree
    print("running with lxml.etree")
except ImportError:
    import xml.etree.ElementTree as etree
    print("running with ElementTree on Python 2.5+")


DOWNLOADS_DIR = os.path.join(module.static_folder, 'downloads')
UPLOADS_DIR = os.path.join(module.static_folder, 'uploads')


def __convert_date(timestamp):
    if os.name == 'nt':
        # Hack for Win (http://stackoverflow.com/questions/10588027/converting-timestamps-larger-than-maxint-into-datetime-objects)
        return date.fromtimestamp(0) + timedelta(seconds=timestamp / 1000)
    return date.fromtimestamp(timestamp / 1000)


def datetimeformat(value, _format='%Y-%m-%d'):
    if isinstance(value, datetime):
        return value.strftime(_format)
    elif isinstance(value, int) or isinstance(value, long):
        return __convert_date(value).strftime(_format)
    else:
        return None


class XML_Registry(object):

    def __init__(self,
                 contract_id,
                 start,
                 end,
                 infis_code,
                 primary,
                 tags,
                 departments=list()):

        self.client = Client(_config('core_service_url'))
        self.contract_id = contract_id
        self.start = start
        self.end = end
        self.infis_code = infis_code
        self.patient_tags = tags.get('patients', list())
        self.event_tags = tags.get('services', list())
        self.primary = primary
        self.departments = departments

    def __patient_optional_tags(self):
        result = []
        patient_events_tags = self.patient_tags
        patient_events_tags.extend(self.event_tags)
        for tag in patient_events_tags:
            try:
                attr = getattr(PatientOptionalFields, tag)
            except exceptions.AttributeError:
                pass
            else:
                result.append(attr)
        return result

    def __person_optional_tags(self):
        result = []
        patient_events_tags = self.patient_tags
        patient_events_tags.extend(self.event_tags)
        for tag in patient_events_tags:
            try:
                attr = getattr(PersonOptionalFields, tag)
            except exceptions.AttributeError:
                pass
            else:
                result.append(attr)
        return result

    def __event_optional_tags(self):
        result = []
        for tag in self.event_tags:
            try:
                attr = getattr(SluchOptionalFields, tag)
            except exceptions.AttributeError:
                pass
            else:
                result.append(attr)
        return result

    def get_data(self):
        data = self.client.get_xml_registry(contract_id=self.contract_id,
                                            infis_code=self.infis_code,
                                            old_infis_code=_config('old_lpu_infis_code'),
                                            start=self.start,
                                            end=self.end,
                                            smo_number=_config('smo_number'),
                                            primary=self.primary,
                                            departments=self.departments,
                                            mo_level=_config('mo_level'),
                                            patient_optional=self.__patient_optional_tags(),
                                            person_optional=self.__person_optional_tags(),
                                            event_optional=self.__event_optional_tags())
        return data


class Services(object):

    def __init__(self, start, end, infis_code, tags):
        self.client = Client(_config('core_service_url'))
        self.start = start
        self.end = end
        self.infis_code = infis_code
        self.tags = tags

    def __filter_tags(self, tags):
        result = []
        for tag in tags:
            try:
                attr = getattr(SluchOptionalFields, tag)
            except exceptions.AttributeError, e:
                print e
            else:
                result.append(attr)
        return list(set(result))

    def __get_ammount(self, services):
        ammount = 0.0
        if not services:
            return ammount
        for key, event_list in services.iteritems():
            if event_list:
                for event in event_list:
                    ammount += getattr(event, 'SUMV', 0)
        return ammount

    def __get_bill(self, services):
        #TODO: инкрементировать номер пакета (01)?
        data = dict(CODE=1,
                    CODE_MO=_config('lpu_infis_code'),
                    YEAR=self.start.strftime('%Y'),
                    MONTH=self.start.strftime('%m'),
                    NSCHET='%s-%s/%s' % (self.end.strftime('%y%m'), '01', _config('old_lpu_infis_code')[0:3]),
                    DSCHET=date.today().strftime('%Y-%m-%d'),
                    PLAT=_config('payer_code'),
                    SUMMAV=self.__get_ammount(services))
        return data


class DBF_Data(object):

    def __init__(self, start, end, infis_code):
        self.client = Client(_config('core_service_url'))
        self.start = start
        self.end = end
        self.infis_code = infis_code

    def get_data(self):
        pass


class DBF_Policlinic(DBF_Data):

    def get_data(self):
        data = self.client.get_policlinic_dbf(infis_code=self.infis_code,
                                              start=self.start,
                                              end=self.end)
        return data


class DBF_Hospital(DBF_Data):

    def get_data(self):
        data = self.client.get_hospital_dbf(infis_code=self.infis_code,
                                            start=self.start,
                                            end=self.end)
        return data


class DownloadWorker(object):

    def __get_download_type(self, template_ids):
        template = db.session.query(Template).filter(Template.id.in_(template_ids)).first()
        return getattr(getattr(template.type, 'download_type', None), 'code', None)

    def __get_templates(self, template_ids):
        return db.session.query(Template).filter(Template.id.in_(template_ids)).all()

    def __get_template_tree(self, template_id):
        root = (db.session.query(TagsTree)
                .filter(TagsTree.template_id == template_id, TagsTree.parent_id == None)
                .first())
        # tree = TagTree(template_id=template_id, root=0)
        # return tree.load_tree(0, [])
        return [root]

    def __tags_list(self, template_id):
        tags = (db.session.query(Tag.code)
                .join(TagsTree)
                .filter(TagsTree.template_id == template_id)
                .order_by(TagsTree.ordernum).all())
        tags = [tag[0] for tag in tags]
        # tags = list()
        # for item in tree:
        #     tags.append(item.tag.code)
        return tags

    def __get_conditions(self):
        return None

    def get_data(self, download_type, **kwargs):
        if download_type == 'xml':
            data = XML_Registry(**kwargs).get_data()
        elif download_type == ('dbf', 'policlinic'):
            if 'tags' in kwargs:
                del kwargs['tags']
            data = DBF_Policlinic(**kwargs).get_data()
        elif download_type == ('dbf', 'hospital'):
            if 'tags' in kwargs:
                del kwargs['tags']
            data = DBF_Hospital(**kwargs).get_data()
        else:
            raise NameError
        return data

    def __get_file_object(self, template_type, end, tags):
        return File.provider(data_type=template_type[1], end=end, file_type=template_type[0], tags=tags)

    def do_download(self, template_ids, infis_code, contract_id, start, end, primary, departments=list()):
        tags, tree, files = dict(), dict(), dict()
        template, download_type = None, None
        templates = self.__get_templates(template_ids)
        for template in templates:
            tags[template.type.code] = self.__tags_list(template.id)
            tree[template.type.code] = self.__get_template_tree(template.id)

        if not tree:
            return None

        if template:
            download_type = getattr(getattr(template.type, 'download_type', None), 'code', None)

        data = self.get_data(download_type=download_type,
                             infis_code=infis_code,
                             contract_id=int(contract_id),
                             start=start,
                             end=end,
                             primary=primary,
                             tags=tags,
                             departments=departments)

        if not getattr(data, 'registry', None):
            exception = exceptions.ValueError()
            exception.message = u'За указанный период услуг не найдено'
            raise exception

        for template in templates:
            file_obj = self.__get_file_object((download_type, template.type.code),
                                              end=end,
                                              tags=tags[template.type.code])
            files[template.type.code] = file_obj.save_file(tree[template.type.code], data)

            if template.archive:
                files[template.type.code] = file_obj.archive_file()

        return files


class DownloadHistory(object):

    def add_file(self):
        pass


class UploadWorker(object):

    policy_fields = dict(SPOLIS='serial', NPOLIS='number', VPOLIS='policyTypeCode', SMO='insurerInfisCode')

    def __init__(self):
        self.client = Client(_config('core_service_url'))

    def do_upload(self, file_path):
        data = self.__parse(file_path)
        return self.client.load_tfoms_payments(data)

    def __patient(self, element):
        # TODO: legagy, clean
        data = dict()
        patient_id = None
        for child in element:
            if child.tag == 'ID_PAC':
                patient_id = int(child.text)
            elif child.tag == 'VPOLIS':
                data[child.tag] = int(child.text)
            else:
                data[child.tag] = child.text
        report = Reports()
        result = report.update_patient(patient_id, data)
        if result:
            policy_data = dict()
            for key, value in data.iteritems():
                if key in self.policy_fields:
                    policy_data[self.policy_fields[key]] = value

            policy_data = TClientPolicy(**policy_data)
            try:
                client_result = self.client.update_policy(patient_id, policy_data)
            except NotFoundException, e:
                print e
            except TException, e:
                print e
            else:
                pass

    def __get_filename(self, root):
        for element in root.iter('ZGLV'):
            for child in element:
                if child.tag.lower() == 'filename':
                    filename = child.text
                    return filename

    def __get_nschet(self, root):
        for element in root.iter('SCHET'):
            for child in element:
                if child.tag.lower() == 'nschet':
                    nschet = child.text
                    return nschet

    def __get_case(self, element):
        # TODO: переделать перебор тегов на find?
        payment = Payment()
        confirmed = False
        sumv = 0.0
        for child in element:
            if child.tag.lower() == 'idcase':
                payment.accountItemId = int(child.text)
            elif child.tag.lower() == 'refreason':
                payment.refuseTypeCode = child.text
                if child.text == '0':
                    confirmed = True
                else:
                    confirmed = False
            elif child.tag.lower() == 'comentsl':
                payment.comment = child.text
            elif child.tag.lower() == 'sumv':
                sumv = float(child.text)
        return payment, confirmed, sumv

    def __parse(self, file_path):
        data = dict(payments=list(), refusedAmount=0, payedAmount=0, payedSum=0.0, refusedSum=0.0, comment='')

        if os.path.isfile(file_path):
            try:
                tree = etree.parse(file_path)
            except etree.XMLSyntaxError, e:
                raise AttributeError(u'Некорректная структура XML: {0}'.format(e))
            root = tree.getroot()
            filename = self.__get_filename(root)
            if filename:
                #data['fileName'] = '{0}.xml'.format(filename)
                data['fileName'] = filename
            else:
                raise AttributeError(u'Не заполнен тег FILENAME')
            nschet = self.__get_nschet(root)
            if nschet:
                data['accountNumber'] = nschet
            else:
                raise AttributeError(u'Не заполнен тег NSCHET')
            for element in root.iter('ZAP'):
                for child in element:
                    if child.tag.lower() == 'sluch':
                        payment, confirmed, sumv = self.__get_case(child)
                        data['payments'].append(payment)
                        if confirmed is True:
                            data['payedAmount'] += 1
                            data['payedSum'] += sumv
                        else:
                            data['refusedAmount'] += 1
                            data['refusedSum'] += sumv
        return data


class File(object):

    @classmethod
    def provider(cls, data_type, end, file_type='xml', tags=[]):
        """Вернёт объект для работы с указанным типом файла"""
        file_type = file_type.lower()
        if file_type == 'xml':
            obj = XML(data_type, end)
        elif file_type == 'dbf':
            obj = DBF(data_type, end, tags=tags)
        else:
            raise exceptions.NameError
        return obj


class XML(object):

    def __init__(self, data_type, end):
        self.data_type = data_type
        self.end = end
        self.file_name = None
        self.head = None
        self.dir_name = None

        if self.data_type == 'patients':
            self.template = 'tfoms/xml/patients.xml'
        elif self.data_type == 'services':
            self.template = 'tfoms/xml/services.xml'
        else:
            raise exceptions.NameError

    def generate_filename(self, data):
        if self.data_type == 'patients':
            self.file_name = data.patientRegistryFILENAME
        elif self.data_type == 'services':
            self.file_name = data.serviceRegistryFILENAME
        else:
            raise exceptions.NameError

    def generate_file(self, tags_tree, data):
        env = Environment(loader=PackageLoader(module.import_name,
                                               module.template_folder))
        env.filters['datetimeformat'] = datetimeformat

        template = env.get_template(self.template)
        linked_file = XML(data_type='services', end=self.end)
        linked_file.generate_filename(data)
        self.head = dict(VERSION='1.0',
                         DATA=date.today().strftime('%Y-%m-%d'),
                         FILENAME=self.file_name,
                         FILENAME1=linked_file.file_name)

        return template.render(encoding=_config('xml_encoding'), head=self.head, tags_tree=tags_tree, data=data)

    def __create_download_dir(self, account):
        self.dir_name = str(account.id)
        path = os.path.join(DOWNLOADS_DIR, self.dir_name)
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def save_file(self, tags_tree, data):
        self.generate_filename(data)
        content = self.generate_file(tags_tree, data)
        self.__create_download_dir(data.account)
        f = open(os.path.join(DOWNLOADS_DIR, self.dir_name, '%s.xml' % self.file_name), 'w')
        f.write(content.encode(_config('xml_encoding')))
        f.close()
        return self.dir_name, '{0}.xml'.format(self.file_name)

    def archive_file(self):
        with ZipFile(
                os.path.join(DOWNLOADS_DIR, self.dir_name, '{0}.xml.zip'.format(self.file_name)),
                'w',
                ZIP_DEFLATED) as archive:
            archive.write(
                os.path.join(DOWNLOADS_DIR, self.dir_name, '{0}.xml'.format(self.file_name)),
                '%s.xml' % self.file_name)
        return self.dir_name, '{0}.xml.zip'.format(self.file_name)


class DBF(object):

    def __init__(self, data_type, end, tags):
        self.data_type = data_type
        self.end = end
        self.tags = tags

    def __get_month(self, date):
        monthes = range(13)
        monthes[10] = 'a'
        monthes[11] = 'b'
        monthes[12] = 'c'
        month = date.month
        if month > 9:
            month = monthes[month]
        return month

    def generate_filename(self):
        self.file_name = 'L'
        self.file_name += str(self.__get_org_type())
        self.file_name += _config('old_lpu_infis_code')

        self.arj_file_name = '10'
        self.arj_file_name += _config('old_lpu_infis_code')
        self.arj_file_name += '%s' % self.end.strftime('%d')
        self.arj_file_name += '%s' % self.__get_month(self.end)

    def __get_field_type(self, value, tag):
        if isinstance(value, basestring):
            _type = 'C(254)'
        elif isinstance(value, date):
            _type = 'D'
        elif isinstance(value, int):
            _type = 'N(10,0)'
        elif isinstance(value, float):
            _type = 'N(7,2)'
        else:
            _type = 'C(254)'

        if tag == 'KOD_LPU':
            _type = 'N(10,0)'
        elif tag == 'DAT_SC':
            _type = 'D'
        elif tag == 'VL':
            _type = 'N(10,0)'
        return _type

    def __generate_fields(self, tags, row):
        # NOT USED
        env = Environment(loader=PackageLoader(module.import_name, module.template_folder))
        env.filters['datetimeformat'] = datetimeformat

        template = env.get_template('dbf/fields')
        return str(template.render(tags=tags).lstrip())

    def __get_org_type(self):
        _type = None
        if self.data_type == 'hospital':
            _type = 1
        elif self.data_type == 'policlinic':
            _type = 2
        return _type

    def __generate_bill_number(self, num):
        bill_num = _config('old_lpu_infis_code')
        bill_num += str(self.__get_org_type())
        bill_num += '_'  #TODO: исправленный, то W
        bill_num += 'M'  #TODO: убедиться, что других случаев нет
        bill_num += '{0:04d}'.format(num)
        return bill_num

    def generate_file(self, tags, data):
        dbf.input_decoding = 'utf8'
        dbf.default_codepage = 'utf8'
        fields = []
        for key, item in enumerate(data):
            if key == 0:
                for tag in tags:
                    fields.append('{0} {1}'.format(tag.strip(), self.__get_field_type(getattr(item, tag, ''), tag)))
                table = dbf.Table(os.path.join(DOWNLOADS_DIR, '%s.dbf' % self.file_name), '; '.join(fields))
                table.open()

            row = []
            for tag in tags:
                value = getattr(item, tag, '')
                if tag == 'N_CH':
                    value = self.__generate_bill_number(key + 1)
                elif tag == 'KOD_LPU':
                    value = _config('lpu_infis_code')
                elif tag == 'DAT_SC':
                    value = date.today()
                elif tag == 'VL':
                    value = self.__get_org_type()
                if isinstance(value, date):
                    value = dbf.Date(value.year, value.month, value.day)
                row.append(value)
            table.append(tuple(row))
        table.close()
        return table

    def save_file(self, tags, data):
        self.generate_filename()
        dbf_file = self.generate_file(self.tags, data)
        return '%s.dbf' % self.file_name

    def archive_file(self):
        import patoolib
        patoolib.create_archive(os.path.join(DOWNLOADS_DIR, '%s.arj' % self.arj_file_name),
                                (os.path.join(DOWNLOADS_DIR, '%s.dbf' % self.file_name), ))
        return '%s.arj' % self.arj_file_name


class Utility(object):

    def prepare_table(self, table_type):
        """Проверяет насколько давно было обновление таблицы с данными
        и при необходимости посылает запрос ядру на обновление таблицы

        """
        pass


class Contracts(object):

    def get_contracts(self, infis_code):
        client = Client(_config('core_service_url'))
        return client.get_contracts(infis_code)