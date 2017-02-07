# -*- coding: utf-8 -*-

from collections import OrderedDict

__author__ = 'mmalkov'

request_type_pregnancy = 'pregnancy'
request_type_gynecological = 'gynecological'

risar_mother_anamnesis = 'risar_mother_anamnesis'
risar_father_anamnesis = 'risar_father_anamnesis'
risar_epicrisis = 'epicrisis'
risar_newborn_inspection = 'risar_newborn_inspection'

risar_anamnesis_pregnancy = 'risar_anamnesis_pregnancy'
risar_anamnesis_transfusion = 'risar_anamnesis_transfusion'

risar_gyn_general_anamnesis_flat_code = 'gynecological_visit_general_anamnesis'
risar_gyn_checkup_flat_code = 'gynecological_visit_general_checkUp'
risar_gyn_checkup_flat_codes = (risar_gyn_checkup_flat_code,)

pregnancy_card_attrs = 'cardAttributes'
gynecological_card_attrs = 'gynecologicalAttributes'
gynecological_ticket_25 = 'gynecological_ticket_25'

pregnancy_apt_codes = [
    'year', 'pregnancyResult', 'pregnancy_week', 'note', 'preeclampsia', 'pregnancy_pathology',
    'delivery_pathology', 'maternity_aid', 'after_birth_complications', 'operation_testimonials',
]
transfusion_apt_codes = ['year', 'type', 'reaction']

risar_anamnesis_apt_common_codes = [
    'education', 'work_group', 'professional_properties',
    'infertility', 'infertility_period', 'infertility_cause', 'infertility_type', 'infertility_treatment',
    'blood_type', 'finished_diseases', 'current_diseases', 'finished_diseases_text', 'current_diseases_text',
    'hereditary', 'hereditary_defect', 'hereditary_free_input', 'alcohol', 'smoking', 'toxic', 'drugs']

risar_anamnesis_apt_mother_codes = [
    'menstruation_last_date', 'marital_status',
    'menstruation_start_age', 'menstruation_duration', 'menstruation_period', 'menstruation_disorders',
    'intrauterine', 'sex_life_start_age', 'contraception', 'fertilization_type', 'family_income',
    'preeclampsia', 'multifetation', 'heart_disease', 'attempt_number'] + risar_anamnesis_apt_common_codes
risar_anamnesis_apt_father_codes = ['name', 'phone', 'HIV', 'fluorography', 'age'] + risar_anamnesis_apt_common_codes

first_inspection_flat_code = 'risarFirstInspection'
second_inspection_flat_code = 'risarSecondInspection'
pc_inspection_flat_code = 'risarPCCheckUp'
puerpera_inspection_flat_code = 'risarPuerperaCheckUp'

checkup_flat_codes = (first_inspection_flat_code, second_inspection_flat_code, pc_inspection_flat_code)

# рассматривать все осмотры из следующих как непрерывную последовательность;
# используется в определении порядка следования осмотров при расчете диагнозов,
# закрытии предыдущих, а также в методах интеграции
inspections_span_flatcodes = tuple(checkup_flat_codes + (puerpera_inspection_flat_code,))

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

gyn_checkup_simple_codes = [
    'last_menstruation_date',
    'last_menstruation_features',
    'last_menstruation_character',
    'libido',
    'intercourse_partner',
    'sexual_intercourse',
    'contraception',
    'medicament',
    'pain_location',
    'pain_how_long',
    'pain_character',
    'temperature_rise',
    'shivers',
    'menstrual_disorders',
    'discharge_consistency',
    'discharge_colour',
    'discharge_quantity',
    'discharge_smell',
    'itch_character',
    'itch_period',
    'pregnancy_failure',
    'pregnancy_failure_period',
    'engorged_breasts',
    'breasts_pain',
    'breasts_induration',
    'nipples_discharge',
    'other_complaints',
    'weight',
    'height',
    'mrk',
    'imt',
    'temperature',
    'heart_rate',
    'AD_right_high',
    'AD_right_low',
    'AD_left_high',
    'AD_left_low',
    'skin',
    'mucous',
    'lymph_which',
    'lymph',
    'subcutaneous_fat',
    'breast',
    'nipples',
    'stomach',
    'stomach_area',
    'pilosis',
    'comments',
    'vulva_pilosis',
    'vulva_skin',
    'vulva_skin_adds',
    'groin_glands',
    'vulva_mucous',
    'vulva_mucous_adds',
    'vulva_germination',
    'urethra',
    'urethra_adds',
    'perianal_zona',
    'vulva_discharge_consistency',
    'vulva_discharge_colour',
    'vulva_discharge_quantity',
    'vulva_discharge_smell',
    'vulva_comments',
    'vagina_mirrors_mirrors',
    'vagina_mirrors_adds',
    'vagina_paries_mirrors',
    'vagina_paries_mirrors_other',
    'cervix_uteri_mirrors',
    'cervix_uteri_size_mirrors',
    'cervix_uteri_shape_mirrors',
    'anabrosis_mirrors',
    'ectropion_mirrors',
    'uterus_external_orifice_mirrors',
    'vaginal_fornix_mirrors',
    'vaginal_fornix_adds_mirrors',
    'mucous_mirrors',
    'mucous_adds_mirrors',
    'discharge_consistency_mirrors',
    'discharge_colour_mirrors',
    'discharge_quantity_mirrors',
    'discharge_smell_mirrors',
    'comments_mirrors',
    'bimanual_cervix_uteri',
    'bimanual_cervix_consistency',
    'bimanual_uterus_body',
    'bimanual_body_of_womb_size',
    'bimanual_body_of_womb_enlarged',
    'bimanual_uteri_position',
    'bimanual_ovary_right',
    'bimanual_ovary_right_oher',
    'bimanual_ovary_left',
    'bimanual_ovary_left_oher',
    'bimanual_uterine_tubes_right',
    'bimanual_uterine_tubes_left',
    'bimanual_vaginal_fornix',
    'bimanual_formix_other',
    'bimanual_comments',
    'rectovaginal_cervix_uteri',
    'rectovaginal_cervix_consistency',
    'rectovaginal_uterus_body',
    'rectovaginal_body_of_womb_size',
    'rectovaginal_body_of_womb_enlarged',
    'rectovaginal_uteri_position',
    'rectovaginal_parametrium',
    'rectovaginal_parametrium_other',
    'rectovaginal_ovary_right',
    'rectovaginal_ovary_right_oher',
    'rectovaginal_ovary_left',
    'rectovaginal_ovary_left_oher',
    'rectovaginal_uterine_tubes_right',
    'rectovaginal_uterine_tubes_left',
    'rectovaginal_vaginal_fornix',
    'rectal_formix_other',
    'rectovaginal_comments',
    'rectal_perianal_zona',
    'rectal_rectum',
    'rectal_cervix_uteri',
    'rectal_cervix_consistency',
    'rectal_uterus_body',
    'rectal_body_of_womb_size',
    'rectal_body_of_womb_enlarged',
    'rectal_uteri_position',
    'rectal_parametrium',
    'rectal_parametrium_other',
    'rectal_ovary_right',
    'rectal_ovary_right_oher',
    'rectal_ovary_left',
    'rectal_ovary_left_oher',
    'rectal_uterine_tubes_right',
    'rectal_uterine_tubes_left',
    'rectal_vaginal_fornix',
    'rectovaginal_formix_other',
    'rectal_comments',
    'encompassing_comments',
    'encompassing_treatment',
    'treatment_recommendations',
]

gyn_checkup_codes = gyn_checkup_simple_codes + ['ticket_25']


soc_prof_codes = OrderedDict(
    (('mother_employment', ['date', 'explanation', 'gestation_age', 'failure_reason']),
     ('sanatorium_therapy', ['failure_reason', 'results', 'doctor', 'gestation_age', 'name']),
     ('gymnastics', ['gestation_age', 'lessons_number', 'doctor', 'failure_reason']),
     ('maternity_lessons', ['failure_reason', 'doctor', 'lessons_number', 'gestation_age']),
     ('psychological_preparation', ['failure_reason', 'doctor', 'lessons_number', 'gestation_age']),
     ('legal_support', ['gestation_age', 'explanation', 'doctor', 'failure_reason'])))

nursing = dict(
    (('prepartal_nursing', ['date', 'gestational_age', 'vacation_date', 'profession_husband', 'children',
                           'other_family_members', 'living_conditions', 'psychological_environment', 'mother_health',
                           'father_health', 'children_health', 'other_family_members_health', 'biological_anamnesis',
                           'acute_disease', 'flareup_chronic_condition', 'operations', 'fetal_infection', 'medicines',
                           'womens_consultation_clinic_visiting', 'maternity_school', 'day_regimen', 'nutrition',
                           'hypogalactia', 'child_risk', 'recommendations', 'profession']),
    ('prepartal_nursing_repeat', ['date', 'gestational_age', 'arragements_completion', 'conditions_of_work',
                                  'conditions_of_living', 'regimen', 'nutrition', 'corrective_measures',
                                  'sanitation', 'sanitary_condition', 'newborn_acceptance_readiness',
                                  'hypogalactia', 'child_risk', 'recommendations']),
    ('postpartal_nursing', ['date', 'day_of_age', 'day_of_leaving', 'complaints', 'infant_feeding',
                            'feeding_status', 'general_habitus', 'weight', 'height', 'chest_circumference',
                            'head_circumference', 'physiologic_reflex', 'muscle_tone', 'body_build', 'skin', 'mucous',
                            'skull', 'rhaphe', 'fontanel', 'collar_bone', 'hip_joint', 'chest_shape', 'breathe_character',
                            'breathe_frequency', 'heart_vascular_system', 'heart_rate', 'umbilical_wound',
                            'stomach_status', 'stomach_circumference', 'liver', 'spleen', 'genitals',
                            'urination', 'family', 'social_conditions', 'newborn_care', 'conclusion',
                            'plan', 'recommendations']))
)


pregnancy_card_apts = ['prenatal_risk_572', 'predicted_delivery_date', 'pregnancy_start_date', 'preeclampsia_risk',
                       'chart_modify_date', 'chart_modify_time', 'pregnancy_pathology_list',
                       'preeclampsia_susp', 'preeclampsia_comfirmed', 'card_fill_rate', 'card_fill_rate_anamnesis',
                       'card_fill_rate_first_inspection', 'card_fill_rate_repeated_inspection',
                       'card_fill_rate_epicrisis', 'pregnancy_start_date_by_ultrasonography', 'pdd_mensis']
