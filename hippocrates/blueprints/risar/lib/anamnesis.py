# -*- coding: utf-8 -*-


def copy_anamnesis_from_gyn_card(gyn_card, preg_card):
    preg_card.anamnesis.mother['menstruation_start_age'].value = gyn_card.anamnesis['age'].value
    preg_card.anamnesis.mother['menstruation_duration'].value = gyn_card.anamnesis['duration'].value
    preg_card.anamnesis.mother['menstruation_period'].value = gyn_card.anamnesis['period_duration'].value
    preg_card.anamnesis.mother['menstruation_disorders'].value = gyn_card.anamnesis['disorder'].value
    preg_card.anamnesis.mother['sex_life_start_age'].value = gyn_card.anamnesis['sex_life_age'].value
    preg_card.anamnesis.mother['marital_status'].value = gyn_card.anamnesis['marital_status'].value
    preg_card.anamnesis.mother['infertility'].value = gyn_card.anamnesis['infertility'].value
    preg_card.anamnesis.mother['infertility_type'].value = gyn_card.anamnesis['infertility_kind'].value
    preg_card.anamnesis.mother['infertility_period'].value = gyn_card.anamnesis['infertility_duration'].value
    preg_card.anamnesis.mother['infertility_cause'].value = gyn_card.anamnesis['infertility_etiology'].value
    preg_card.anamnesis.mother['infertility_treatment'].value = gyn_card.anamnesis['infertility_treatment'].value
    preg_card.anamnesis.mother['alcohol'].value = gyn_card.anamnesis['alcohol'].value
    preg_card.anamnesis.mother['smoking'].value = gyn_card.anamnesis['smoking'].value
    preg_card.anamnesis.mother['toxic'].value = gyn_card.anamnesis['toxic'].value
    preg_card.anamnesis.mother['drugs'].value = gyn_card.anamnesis['drugs'].value
    preg_card.anamnesis.mother['work_group'].value = gyn_card.anamnesis['work_group'].value
    preg_card.anamnesis.mother['professional_properties'].value = gyn_card.anamnesis['professional_properties'].value