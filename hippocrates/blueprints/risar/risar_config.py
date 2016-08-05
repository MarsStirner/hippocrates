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

risar_gyn_general_anamnesis_code = 'gynecological_visit_general_anamnesis'
risar_gyn_checkup_code = 'gynecological_visit_general_checkUp'
risar_gyn_checkup_codes = (risar_gyn_checkup_code,)

pregnancy_card_attrs = 'cardAttributes'
gynecological_card_attrs = 'gynecologicalAttributes'
gynecological_ticket_25 = 'gynecological_ticket_25'

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
    'preeclampsia', 'multifetation', 'heart_disease'] + common_codes
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
    'heart _rate',
    'AD_right_high',
    'AD_right_low',
    'AD_left_high',
    'AD_left_low',
    'skin',
    'mucous',
    'lymph',
    'subcutaneous_fat',
    'breast',
    'nipples',
    'stomach',
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
    'cervix_uteri_mirrors',
    'cervix_uteri_size_mirrors',
    'cervix_uteri_shape_mirrors',
    'anabrosis_mirrors',
    'ectropion_mirrors',
    'uterus_external_orifice_mirrors',
    'vaginal_fornix_mirrors',
    'vaginal_fornix_adds_mirrors',
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
    'rectal_comments',
    'encompassing_comments',
    'encompassing_treatment',
    'treatment_recommendations',
]

gyn_checkup_codes = gyn_checkup_simple_codes + ['ticket_25']
