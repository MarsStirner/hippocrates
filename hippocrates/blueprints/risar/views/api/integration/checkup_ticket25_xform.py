# -*- coding: utf-8 -*-
import logging

from abc import abstractmethod

from hippocrates.blueprints.risar.views.api.integration.xform import XForm, wrap_simplify
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema
from hippocrates.blueprints.risar.lib.represent.common import represent_action_diagnoses
from hippocrates.blueprints.risar.lib.specific import SpecificsManager

from nemesis.lib.utils import safe_date, safe_traverse, safe_datetime, safe_dict, safe_int, safe_bool_none
from nemesis.lib.apiutils import json_dumps
from nemesis.models.person import Person
from nemesis.models.exists import rbDiseaseCharacter, rbTraumaType, MKB, rbAcheResult, rbFinance, rbResult
from nemesis.models.risar import rbConditionMedHelp, rbProfMedHelp
from nemesis.systemwide import db


logger = logging.getLogger('simple')


class CheckupsTicket25XFormSchema(Schema):
    """
    Схемы для проверки валидности данных талона посещения
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "ticket",
            "description": "Талон",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "hospital": {
                    "description": "Место обращения (код ЛПУ)",
                    "type": "string"
                },
                "department": {
                    "description": "Код подразделения",
                    "type": "string"
                },
                "date_open": {
                    "description": "Дата открытия талона",
                    "type": "string",
                    "format": "date"
                },
                "date_close": {
                    "description": "Дата закрытия талона",
                    "type": "string",
                    "format": "date"
                },
                "medical_care": {
                    "description": "Оказываемая медицинская помощь, справочник rbRisarMedicalCare",
                    "type": "string"
                },
                "medical_care_emergency": {
                    "description": "Форма оказания медицинской помощи (неотложная - да/нет)",
                    "type": "boolean"
                },
                "medical_care_profile": {
                    "description": "Профиль медицинской помощи, справочник rbProfMedHelp",
                    "type": "string"
                },
                "medical_care_place": {
                    "description": "Условия(место) оказания медицинской помощи, справочник rbConditionMedHelp",
                    "type": "string"
                },
                "children": {
                    "description": "Детское обращение (пациентка до 14 лет - да/нет)",
                    "type": "boolean"
                },
                "visit_place": {
                    "description": "Место посещения (оказания медицинской помощи), справочник rbRisarVisitPlace",
                    "type": "string"
                },
                "visit_type": {
                    "description": "Посещение (тип), справочник rbRisarVisit_Type",
                    "type": "string"
                },
                "finished_treatment": {
                    "description": "Обращение (законченный случай лечения), справочник rbRisarFinishedTreatment",
                    "type": "string"
                },
                "initial_treatment": {
                    "description": "Обращение (первичность), справочник rbRisarInitialTreatment",
                    "type": "string"
                },
                "treatment_result": {
                    "description": "Результат обращения, справочник rbResult",
                    "type": "string"
                },
                "disease_outcome": {
                    "description": "Исход заболевания, справочник rbAcheResult",
                    "type": "string"
                },
                "payment": {
                    "description": "Оплата за счет, справочник rbFinance",
                    "type": "string"
                },
                "visit_dates": {
                    "description": "Даты посещений",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "date"
                    },
                    "minItems": 1
                },
                "preliminary_diagnosis": {
                    "description": "Диагноз предварительный (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "preliminary_reason": {
                    "description": "Внешняя причина (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "medical_services": {
                    "description": "Медицинские услуги",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "medical_service": {
                                "description": "Медицинская услуга (код)",
                                "type": "string"
                            },
                            "medical_service_quantity": {
                                "description": "Медицинская услуга, количество",
                                "type": "string"
                            },
                            "medical_service_doctor": {
                                "description": "Врач, оказавший услугу (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "diagnosis": {
                    "description": "Диагноз заключительный (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "reason": {
                    "description": "Внешняя причина (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "diagnosis_sop": {
                    "description": "Сопутствующие заболевания",
                    "type": "array",
                    "items": {
                        "description": "Сопутствующее заболевание (код МКБ)",
                        "type": "string",
                        "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                    }
                },
                "disease_character": {
                    "description": "Заболевание, справочник rbDiseaseCharacter",
                    "type": "string"
                },
                "dispensary": {
                    "description": "Диспансерное наблюдение, справочник rbDispancer",
                    "type": "string"
                },
                "trauma": {
                    "description": "Травма, справочник rbTraumaType",
                    "type": "string"
                },
                "operations": {
                    "description": "Операции",
                    "type": "array",
                    "items": {
                        "description": "Операция",
                        "type": "object",
                        "properties": {
                            "operation_code": {
                                "description": "Операция (код)",
                                "type": "string"
                            },
                            "operation_anesthesia": {
                                "description": "Анестезия, справочник rbRisarOperationAnesthetization",
                                "type": "string"
                            },
                            "operation_equipment": {
                                "description": "Операция проведена с использованием аппаратуры, справочник rbRisarOperationEquipment",
                                "type": "string"
                            },
                            "operation_doctor": {
                                "description": "Врач операции (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "manipulations": {
                    "description": "Манипуляции, исследования",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "manipulation": {
                                "description": "Манипуляция, исследование (код)",
                                "type": "string"
                            },
                            "manipulation_quantity": {
                                "description": "Манипуляция, количество",
                                "type": "integer"
                            },
                            "manipulation_doctor": {
                                "description": "Врач манипуляции (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "sick_leaves": {
                    "description": "Документы о временной нетрудоспособности",
                    "type": "array",
                    "items": {
                        "description": "Документ о временной нетрудоспособности",
                        "type": "object",
                        "properties": {
                            "sick_leave_type": {
                                "description": "Документ о временной нетрудоспособности, справочник rbRisarSickLeaveType",
                                "type": "string"
                            },
                            "sick_leave_reason": {
                                "description": "Повод выдачи, справочник rbRisarSickLeaveReason",
                                "type": "string"
                            },
                            "sick_leave_date_open": {
                                "description": "Дата выдачи",
                                "type": "string",
                                "format": "date"
                            },
                            "sick_leave_date_close": {
                                "description": "Дата закрытия",
                                "type": "string",
                                "format": "date"
                            }
                        }
                    }
                },
                "doctor": {
                    "description": "Врач (код врача)",
                    "type": "string"
                }
            },
            "required": ["doctor", "hospital", "diagnosis", "date_open"]
        }
    ]


class CheckupsTicket25XForm(XForm):

    def __init__(self, *args, **kwargs):
        super(CheckupsTicket25XForm, self).__init__(*args, **kwargs)
        self.checkup_xform = None

    @abstractmethod
    def set_checkup_xform(self):
        pass

    def check_params(self, target_obj_id, parent_obj_id=None, data=None):
        if not self.checkup_xform:
            self.set_checkup_xform()

        self.checkup_xform.check_params(target_obj_id, parent_obj_id, data)

    def _find_target_obj_query(self):
        pass

    def check_duplicate(self, data):
        pass

    def find_ticket25(self):
        if not self.checkup_xform:
            self.set_checkup_xform()

        if not self.checkup_xform.target_obj:
            self.checkup_xform.find_target_obj(self.checkup_xform.target_obj_id)
        self.target_obj = self.checkup_xform.target_obj.propsByCode['ticket_25'].value
        self.target_obj.update_action_integrity()

    def log_current_state(self):
        message = u'Данные талона посещения в осмотре с id={0} до сохранения:\n{1}'.format(
            self.checkup_xform.target_obj.id,
            json_dumps(self.as_json())
        )
        logger.info(message, extra=dict(tags=['RISAR_INTGR', 'TICKET25_CS']))

    def format_data(self, data):
        hosp_code = data.get('hospital')
        res = {
            'hospital': self.find_org(data.get('hospital')),
            'department': self.find_org_structure(data.get('department')),
            'person': self.find_doctor(data.get('doctor'), data.get('hospital')),
            'beg_date': safe_datetime(safe_date(data.get('date_open'))),
            'end_date': safe_datetime(safe_date(data.get('date_close'))),
            'urgent': safe_bool_none(data.get('medical_care_emergency')),
            'medical_care': self.to_rb(data.get('medical_care')),
            'prof_med_help': self.rb(data.get('medical_care_profile'), rbProfMedHelp),
            'condit_med_help': self.rb(data.get('medical_care_place'), rbConditionMedHelp),
            'visit_place': self.to_rb(data.get('visit_place')),
            'finished_treatment': self.to_rb(data.get('finished_treatment')),
            'initial_treatment': self.to_rb(data.get('initial_treatment')),
            'treatment_result': self.rb(data.get('treatment_result'), rbResult),
            'visit_type': self.to_rb(data.get('visit_type')),
            'payment': self.rb(data.get('payment'), rbFinance),
            # 'visit_dates': [],  # ignore this
            # 'children': None,  # ignore this
            'services': map(lambda s_data: self._format_service_data(s_data, hosp_code),
                            data.get('medical_services', [])),
            'operations': map(lambda s_data: self._format_operation_data(s_data, hosp_code),
                              data.get('operations', [])),
            'manipulations': map(lambda s_data: self._format_manipulation_data(s_data, hosp_code),
                                 data.get('manipulations', [])),
            'temp_disability': map(lambda s_data: self._format_sick_leave(s_data),
                                   data.get('sick_leaves', [])),

            '_data_for_diags': self._format_diags_data(data)
        }
        return res

    def _format_service_data(self, data, hospital):
        med_service = self._get_rb_service_format(data.get('medical_service'))
        person = self.find_doctor(data.get('medical_service_doctor'), hospital)
        amount = safe_int(data.get('medical_service_quantity'))
        return {
            'service': safe_dict(med_service),
            'person': safe_dict(person),
            'amount': amount
        }

    def _format_operation_data(self, data, hospital):
        service = self._get_rb_service_format(data.get('operation_code'))
        person = self.find_doctor(data.get('operation_doctor'), hospital)
        anes = self.rb(data.get('operation_anesthesia'), 'rbRisarOperationAnesthetization')
        equip = self.rb(data.get('operation_equipment'), 'rbRisarOperationEquipment')
        return {
            'service': safe_dict(service),
            'person': safe_dict(person),
            'anesthetization': safe_dict(anes),
            'equipment': safe_dict(equip)
        }

    def _format_manipulation_data(self, data, hospital):
        service = self._get_rb_service_format(data.get('manipulation'))
        person = self.find_doctor(data.get('manipulation_doctor'), hospital)
        amount = safe_int(data.get('manipulation_quantity'))
        return {
            'service': safe_dict(service),
            'person': safe_dict(person),
            'amount': amount
        }

    def _format_sick_leave(self, data):
        leave_type = self.rb(data.get('sick_leave_type'), 'rbRisarSickLeaveType')
        leave_reason = self.rb(data.get('sick_leave_reason'), 'rbRisarSickLeaveReason')
        beg_date = safe_date(data.get('sick_leave_date_open'))
        end_date = safe_date(data.get('sick_leave_date_close'))
        return {
            'type': safe_dict(leave_type),
            'reason': safe_dict(leave_reason),
            'beg_date': beg_date,
            'end_date': end_date
        }

    def _format_diags_data(self, data):
        diag_data = []
        if 'diagnosis' in data:
            mkb2 = self.rb(data.get('reason'), MKB, 'DiagID')
            character = self.rb(data.get('disease_character'), rbDiseaseCharacter)
            trauma = self.rb(data.get('trauma'), rbTraumaType)
            ache_result = self.rb(data.get('disease_outcome'), rbAcheResult)
            diag_data.append({
                'kind': 'main',
                'mkbs': [data['diagnosis']],
                'additional_info': {
                    data['diagnosis']: {
                        'mkb2': mkb2,
                        'character': character,
                        'trauma': trauma,
                        'ache_result': ache_result
                    }
                }
            })
        if 'diagnosis_sop' in data:
            diag_data.append({
                'kind': 'associated',
                'mkbs': data['diagnosis_sop']
            })
        old_action_data = {
            'begDate': self.checkup_xform.target_obj.begDate,
            'endDate': self.checkup_xform.target_obj.endDate,
            'person': self.checkup_xform.target_obj.person
        }
        return {
            'diags_list': [
                {
                    'diag_data': diag_data,
                    'diag_type': 'final'
                }
            ],
            'old_action_data': old_action_data
        }

    def _get_rb_service_format(self, code):
        refbook = 'rbService_regional' if SpecificsManager.uses_regional_services() else 'SST365'
        return self.rb(code, refbook)

    def update_target_obj(self, data):
        if not self.target_obj:
            self.find_ticket25()

        self.log_current_state()

        data = self.format_data(data)
        data_for_diags = data.pop('_data_for_diags')

        ticket25 = self.target_obj

        ticket25.begDate = data['beg_date']
        ticket25.setPerson = self.target_obj.person = data['person']

        for code, value in data.iteritems():
            if code in ticket25.propsByCode:
                try:
                    prop = ticket25.propsByCode[code]
                    self.check_prop_value(prop, value)
                    prop.value = value
                except Exception, e:
                    logger.error(u'Ошибка сохранения свойства c типом {0}, id = {1}'.format(
                        prop.type.name, prop.type.id), exc_info=True)
                    raise e

        # update data in parent checkup
        self.checkup_xform.target_obj.begDate = data['beg_date']
        if 'department' in self.checkup_xform.target_obj.propsByCode:
            self.checkup_xform.target_obj['department'].value = data['department']

        self.checkup_xform.update_diagnoses_system(
            data_for_diags['diags_list'], data_for_diags['old_action_data']
        )

    def store(self):
        db.session.add(self.target_obj)
        super(CheckupsTicket25XForm, self).store()

    def reevaluate_data(self):
        if not self.checkup_xform:
            self.set_checkup_xform()
        self.checkup_xform.reevaluate_data()

    @wrap_simplify
    def as_json(self):
        if not self.target_obj:
            return

        inspection = self.checkup_xform.target_obj
        action = self.target_obj
        person = action.person
        res = {
            'hospital': self.or_undefined(self.from_org_rb(person and person.organisation)),
            'department': self.or_undefined(
                self.from_org_struct_rb(inspection['department'].value)
                if 'department' in inspection.propsByCode else None
            ),
            'doctor': self.or_undefined(self.from_person_rb(person)),
            'date_open': self.or_undefined(safe_date(action.begDate)),
            'date_close': self.or_undefined(safe_date(action.endDate)),
            'medical_care_emergency': self.or_undefined(safe_bool_none(action['urgent'].value)),
            'medical_care': self.or_undefined(self.from_rb(action['medical_care'].value)),
            'medical_care_profile': self.or_undefined(self.from_rb(action['prof_med_help'].value)),
            'medical_care_place': self.or_undefined(self.from_rb(action['condit_med_help'].value)),
            'visit_place': self.or_undefined(self.from_rb(action['visit_place'].value)),
            'finished_treatment': self.or_undefined(self.from_rb(action['finished_treatment'].value)),
            'initial_treatment': self.or_undefined(self.from_rb(action['initial_treatment'].value)),
            'treatment_result': self.or_undefined(self.from_rb(action['treatment_result'].value)),
            'visit_type': self.or_undefined(self.from_rb(action['visit_type'].value)),
            'payment': self.or_undefined(self.from_rb(action['payment'].value)),
            'visit_dates': self.or_undefined(safe_date(inspection.begDate) and [safe_date(inspection.begDate)]),
            'children': self._repr_is_child(),
            'medical_services': self.or_undefined(self._repr_med_services(action)),
            'operations': self.or_undefined(self._repr_operations(action)),
            'manipulations': self.or_undefined(self._repr_manipulations(action)),
            'sick_leaves': self.or_undefined(self._repr_sick_leaves(action))
        }
        res.update(self._repr_diagnoses_info(inspection))
        return res

    def _repr_is_child(self):
        inspection = self.checkup_xform.target_obj
        return inspection.event.client.age_tuple(inspection.begDate)[3] < 14

    def _repr_med_services(self, action):
        def make_med_service_data(ms):
            doctor_id = safe_traverse(ms, 'person', 'id')
            doctor = Person.query.get(doctor_id) if doctor_id else None
            return {
                'medical_service': safe_traverse(ms, 'service', 'code'),
                'medical_service_doctor': self.from_person_rb(doctor),
                'medical_service_quantity': ms.get('amount')
            }

        return [
            make_med_service_data(ms)
            for ms in action['services'].value
        ]

    def _repr_operations(self, action):
        def make_operation_data(oper):
            doctor_id = safe_traverse(oper, 'person', 'id')
            doctor = Person.query.get(doctor_id) if doctor_id else None
            return {
                'operation_code': safe_traverse(oper, 'service', 'code'),
                'operation_anesthesia': safe_traverse(oper, 'anesthetization', 'code'),
                'operation_equipment': safe_traverse(oper, 'equipment', 'code'),
                'operation_doctor': self.from_person_rb(doctor)
            }
        return [
            make_operation_data(oper)
            for oper in action['operations'].value
        ]

    def _repr_manipulations(self, action):
        def make_manipulation_data(manip):
            doctor_id = safe_traverse(manip, 'person', 'id')
            doctor = Person.query.get(doctor_id) if doctor_id else None
            return {
                'manipulation': safe_traverse(manip, 'service', 'code'),
                'manipulation_doctor': self.from_person_rb(doctor),
                'manipulation_quantity': manip.get('amount')
            }
        return [
            make_manipulation_data(manip)
            for manip in action['manipulations'].value
        ]

    def _repr_sick_leaves(self, action):
        def make_td_data(td):
            return {
                'sick_leave_type': safe_traverse(td, 'type', 'code'),
                'sick_leave_reason': safe_traverse(td, 'reason', 'code'),
                'sick_leave_date_open': safe_date(safe_traverse(td, 'beg_date')),
                'sick_leave_date_close': safe_date(safe_traverse(td, 'end_date')),
            }
        return [
            make_td_data(td)
            for td in action['temp_disability'].value
        ]

    @wrap_simplify
    def _repr_diagnoses_info(self, inspection):
        main_diag = None
        compl_assoc_mkbs = []

        diag_list = represent_action_diagnoses(inspection)
        for diag in diag_list:
            if main_diag is None:
                for diagnosis_kind in diag['diagnosis_types'].values():
                    if diagnosis_kind.code == 'main':
                        main_diag = diag
                        break
                else:
                    compl_assoc_mkbs.append(diag['diagnostic']['mkb'].DiagID)
            else:
                compl_assoc_mkbs.append(diag['diagnostic']['mkb'].DiagID)

        res = {
            'diagnosis_sop': self.or_undefined(compl_assoc_mkbs)
        }
        if main_diag is not None:
            res.update({
                'diagnosis': self.or_undefined(self.from_mkb_rb(main_diag['diagnostic']['mkb'])),
                'reason': self.or_undefined(self.from_mkb_rb(main_diag['diagnostic']['mkb2'])),
                'disease_character': self.or_undefined(self.from_rb(main_diag['diagnostic']['character'])),
                'trauma': self.or_undefined(self.from_rb(main_diag['diagnostic']['trauma'])),
                'disease_outcome': self.or_undefined(self.from_rb(main_diag['diagnostic']['ache_result'])),
            })
        return res
