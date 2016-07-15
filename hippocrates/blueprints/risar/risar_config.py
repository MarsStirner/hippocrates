# -*- coding: utf-8 -*-

__author__ = 'mmalkov'

request_type_pregnancy = 'pregnancy'
request_type_gynecological = 'gynecological'

risar_mother_anamnesis = 'risar_mother_anamnesis'
risar_father_anamnesis = 'risar_father_anamnesis'
risar_epicrisis = 'epicrisis'
risar_newborn_inspection = 'risar_newborn_inspection'

risar_anamnesis_pregnancy = 'risar_anamnesis_pregnancy'
risar_anamnesis_transfusion = 'risar_anamnesis_transfusion'

pregnancy_card_attrs = 'cardAttributes'
gynecological_card_attrs = 'gynecologicalAttributes'

pregnancy_apt_codes = [
    'year', 'pregnancyResult', 'pregnancy_week', 'note', 'preeclampsia', 'pregnancy_pathology',
    'delivery_pathology', 'maternity_aid', 'after_birth_complications'
]
transfusion_apt_codes = ['date', 'type', 'blood_type', 'reaction']

common_codes = [
    'education', 'work_group', 'professional_properties',
    'infertility', 'infertility_period', 'infertility_cause', 'infertility_type', 'infertility_treatment',
    'blood_type', 'finished_diseases', 'current_diseases', 'finished_diseases_text', 'current_diseases_text',
    'hereditary', 'alcohol', 'smoking', 'toxic', 'drugs']

mother_codes = [
    'menstruation_last_date', 'marital_status',
    'menstruation_start_age', 'menstruation_duration', 'menstruation_period', 'menstruation_disorders',
    'intrauterine', 'sex_life_start_age', 'contraception', 'fertilization_type', 'family_income',
    'preeclampsia', 'multifetation'] + common_codes
father_codes = ['name', 'phone', 'HIV', 'fluorography', 'age'] + common_codes

first_inspection_code = 'risarFirstInspection'
second_inspection_code = 'risarSecondInspection'
pc_inspection_code = 'risarPCCheckUp'
puerpera_inspection_code = 'risarPuerperaCheckUp'
checkup_flat_codes = [first_inspection_code, second_inspection_code, pc_inspection_code]

# inspection properties
inspection_preg_week_code = 'pregnancy_week'

attach_codes = {'plan_lpu': '10', 'extra_lpu': '11'}

# Action context codes
general_hospitalizations = 'general_hospitalizations'
general_specialists_checkups = 'general_specialists_checkups'
general_results = 'general_results'


rtc_2_atc = {
    request_type_pregnancy: pregnancy_card_attrs,
    request_type_gynecological: gynecological_card_attrs,
}
