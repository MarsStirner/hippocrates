# -*- coding: utf-8 -*-

__author__ = 'mmalkov'

risar_mother_anamnesis = 'risar_mother_anamnesis'
risar_father_anamnesis = 'risar_father_anamnesis'

risar_anamnesis_pregnancy = 'risar_anamnesis_pregnancy'
risar_anamnesis_transfusion = 'risar_anamnesis_transfusion'

pregnancy_apt_codes = ['number', 'year', 'pregnancyResult', 'alive', 'weight', 'cause_of_death', 'note']
transfusion_apt_codes = ['date', 'type', 'blood_type', 'reaction']

common_codes = ['education', 'work_group', 'professional_properties', 'infertility', 'infertility_period', 'infertility_cause', 'blood_type', 'rh', 'finished_diseases', 'current_diseases', 'hereditary', 'alcohol', 'smoking', 'toxic', 'drugs']
mother_codes = ['menstruation_start_age', 'menstruation_duration', 'menstruation_period', 'menstruation_disorders', 'sex_life_start_age', 'contraception_type', 'natural_pregnancy', 'family_income'] + common_codes
father_codes = ['name'] + common_codes

checkup_flat_codes = ['risarFirstInspection', 'risarSecondInspection']
