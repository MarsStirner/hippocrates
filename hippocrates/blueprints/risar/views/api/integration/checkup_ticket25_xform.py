# -*- coding: utf-8 -*-
import logging

from hippocrates.blueprints.risar.views.api.integration.xform import CheckupsXForm, wrap_simplify
from hippocrates.blueprints.risar.views.api.integration.schemas import Schema

from nemesis.lib.apiutils import ApiException
from nemesis.systemwide import db
from nemesis.lib.utils import safe_date, safe_traverse
from nemesis.models.person import Person


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
                "hospital": {
                    "description": "Место обращения (код ЛПУ)",
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
                        "description": "Медицинская услуга (код)",
                        "type": "string"
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
                "operation": {
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
                            "manipulation_doctor": {
                                "description": "Врач манипуляции (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "sick_leave": {
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
                },
                "doctor": {
                    "description": "Врач (код врача)",
                    "type": "string"
                }
            }
        }
    ]


class CheckupsTicket25XForm(CheckupsXForm):

    def __init__(self, *args, **kwargs):
        super(CheckupsTicket25XForm, self).__init__(*args, **kwargs)
        self.ticket25 = None

    def find_ticket25(self):
        if not self.target_obj:  # == Action inspection
            self.find_target_obj(self.target_obj_id)
        self.ticket25 = self.target_obj.propsByCode['ticket_25'].value

    @wrap_simplify
    def as_json(self):
        self.find_ticket25()
        if not self.ticket25:
            return

        action = self.ticket25
        person = action.person
        res = {
            'hospital': self.or_undefined(self.from_org_rb(person and person.organisation)),
            'doctor': self.or_undefined(self.from_person_rb(person)),
            'date_open': self.or_undefined(safe_date(action.begDate)),
            'date_close': self.or_undefined(safe_date(action.endDate)),
            'medical_care': self.or_undefined(self.from_rb(action['medical_care'].value)),
            'finished_treatment': self.or_undefined(self.from_rb(action['finished_treatment'].value)),
            'initial_treatment': self.or_undefined(self.from_rb(action['initial_treatment'].value)),
            'treatment_result': self.or_undefined(self.from_rb(action['treatment_result'].value)),
            'payment': self.or_undefined(self.from_rb(action['payment'].value)),
            # 'visit_dates': '?',
            # 'preliminary_diagnosis': '?',
            # 'preliminary_reason': '?',
            'medical_services': self.or_undefined(self._repr_med_services(action)),
            # 'diagnosis': '?',
            # 'reason': '?',
            # 'diagnosis_sop': '?',
            # 'disease_character': '?',
            # 'dispensary': '?',
            # 'trauma': '?',
            # 'operation': '?',
            'manipulations': self.or_undefined(self._repr_manipulations(action)),
            # 'sick_leave': '?'
        }

        return res

    def _repr_med_services(self, action):
        return [
            safe_traverse(service, 'service', 'code')
            for service in action['services'].value
        ]

    def _repr_manipulations(self, action):
        def make_manipulation_data(manip):
            doctor_id = safe_traverse(manip, 'person', 'id')
            doctor = Person.query.get(doctor_id) if doctor_id else None
            return {
                'manipulation': safe_traverse(manip, 'service', 'code'),
                'manipulation_doctor': self.from_person_rb(doctor)
            }
        return [
            make_manipulation_data(manip)
            for manip in action['manipulations'].value
        ]
