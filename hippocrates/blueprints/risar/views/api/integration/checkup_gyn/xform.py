# coding: utf-8

from hippocrates.blueprints.risar.lib.represent.gyn import represent_gyn_checkup
from hippocrates.blueprints.risar.lib.utils import get_action_by_id
from hippocrates.blueprints.risar.risar_config import risar_gyn_checkup_flat_code
from hippocrates.blueprints.risar.views.api.integration.checkup_gyn.schemas import \
    CheckupGynSchema
from hippocrates.blueprints.risar.views.api.integration.checkup_ticket25_xform import \
    CheckupsTicket25XFormSchema, CheckupsTicket25XForm
from hippocrates.blueprints.risar.views.api.integration.xform import GynecologyCheckupsXForm
from nemesis.lib.utils import safe_datetime, safe_date
from nemesis.models.actions import ActionType, Action
from nemesis.models.event import Event


class CheckupGynXForm(CheckupGynSchema, GynecologyCheckupsXForm):
    """
    Класс-преобразователь
    """
    parent_obj_class = Event
    target_obj_class = Action

    GENERAL_MAP = {
        'last_menstruation_date': {'attr': 'last_menstruation_date', 'default': None, 'rb': None, 'is_vector': False},
        'last_menstruation_features': {'attr': 'last_menstruation_features', 'default': None,
                                       'rb': 'rbRisarLastMenstruationFeatures', 'is_vector': False},
        'last_menstruation_character': {'attr': 'last_menstruation_character', 'default': [],
                                        'rb': 'rbRisarMenstruationCharacter', 'is_vector': True},
        'libido': {'attr': 'libido', 'default': None, 'rb': 'rbRisarLibido', 'is_vector': False},
        'intercourse_partner': {'attr': 'intercourse_partner', 'default': None,
                                'rb': 'rbRisarIntercoursePartner', 'is_vector': False},
        'sexual_intercourse': {'attr': 'sexual_intercourse', 'default': [],
                               'rb': 'rbRisarSexualIntercourse', 'is_vector': True},
        'contraception': {'attr': 'contraception', 'default': [], 'rb': 'rbContraception', 'is_vector': True},
        'medicament': {'attr': 'medicament', 'default': None, 'rb': None, 'is_vector': False},
        'pain_location': {'attr': 'pain_location', 'default': None, 'rb': None, 'is_vector': False},
        'pain_how_long': {'attr': 'pain_how_long', 'default': None, 'rb': None, 'is_vector': False},
        'pain_character': {'attr': 'pain_character', 'default': [], 'rb': 'rbRisarPainCharacter', 'is_vector': True},
        'temperature_rise': {'attr': 'temperature_rise', 'default': None, 'rb': None, 'is_vector': False},
        'shivers': {'attr': 'shivers', 'default': None, 'rb': None, 'is_vector': False},
        'menstrual_disorders': {'attr': 'menstrual_disorders', 'default': [],
                                'rb': 'rbRisarMenstrualDisorders', 'is_vector': True},
        'discharge_consistency': {'attr': 'discharge_consistency', 'default': [],
                                  'rb': 'rbRisarDischargeConsistency', 'is_vector': True},
        'discharge_colour': {'attr': 'discharge_colour', 'default': None, 'rb': 'rbRisarDischargeColour', 'is_vector': False},
        'discharge_quantity': {'attr': 'discharge_quantity', 'default': None,
                               'rb': 'rbRisarDischargeQuantity', 'is_vector': False},
        'discharge_smell': {'attr': 'discharge_smell', 'default': None, 'rb': 'rbRisarDischargeSmell', 'is_vector': False},
        'itch_character': {'attr': 'itch_character', 'default': [], 'rb': 'rbRisarItchCharacter', 'is_vector': True},
        'itch_period': {'attr': 'itch_period', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_failure': {'attr': 'pregnancy_failure', 'default': None, 'rb': None, 'is_vector': False},
        'pregnancy_failure_period': {'attr': 'pregnancy_failure_period', 'default': None, 'rb': None, 'is_vector': False},
        'engorged_breasts': {'attr': 'engorged_breasts', 'default': None, 'rb': None, 'is_vector': False},
        'breasts_pain': {'attr': 'breasts_pain', 'default': None, 'rb': None, 'is_vector': False},
        'breasts_induration': {'attr': 'breasts_induration', 'default': None, 'rb': None, 'is_vector': False},
        'nipples_discharge': {'attr': 'nipples_discharge', 'default': None, 'rb': None, 'is_vector': False},
        'other_complaints': {'attr': 'other_complaints', 'default': None, 'rb': None, 'is_vector': False},
    }

    OBJECTIVE_MAP = {
        'weight': {'attr': 'weight', 'default': None, 'rb': None, 'is_vector': False},
        'height': {'attr': 'height', 'default': None, 'rb': None, 'is_vector': False},
        'temperature': {'attr': 'temperature', 'default': None, 'rb': None, 'is_vector': False},
        'heart_rate': {'attr': 'heart_rate', 'default': None, 'rb': None, 'is_vector': False},
        'AD_right_high': {'attr': 'AD_right_high', 'default': None, 'rb': None, 'is_vector': False},
        'AD_right_low': {'attr': 'AD_right_low', 'default': None, 'rb': None, 'is_vector': False},
        'AD_left_high': {'attr': 'AD_left_high', 'default': None, 'rb': None, 'is_vector': False},
        'AD_left_low': {'attr': 'AD_left_low', 'default': None, 'rb': None, 'is_vector': False},
        'skin': {'attr': 'skin', 'default': [], 'rb': 'rbRisarSkin', 'is_vector': True},
        'mucous': {'attr': 'mucous', 'default': [], 'rb': 'rbRisarMucous', 'is_vector': True},
        'lymph': {'attr': 'lymph', 'default': [], 'rb': 'rbRisarLymph', 'is_vector': True},
        'subcutaneous_fat': {'attr': 'subcutaneous_fat', 'default': None,
                             'rb': 'rbRisarSubcutaneous_Fat', 'is_vector': False},
        'breast': {'attr': 'breast', 'default': [], 'rb': 'rbRisarBreast', 'is_vector': True},
        'nipples': {'attr': 'nipples', 'default': [], 'rb': 'rbRisarNipples', 'is_vector': True},
        'stomach': {'attr': 'stomach', 'default': [], 'rb': 'rbRisarStomachGenVisit', 'is_vector': True},
        'pilosis': {'attr': 'pilosis', 'default': None, 'rb': None, 'is_vector': False},
        'comments': {'attr': 'comments', 'default': None, 'rb': None, 'is_vector': False},
    }

    VULVA_MAP = {
        'vulva_pilosis': {'attr': 'vulva_pilosis', 'default': None, 'rb': 'rbRisarVulvaPilosis', 'is_vector': False},
        'groin_glands': {'attr': 'groin_glands', 'default': None, 'rb': 'rbRisarGroinGlands', 'is_vector': False},
        'vulva_skin': {'attr': 'vulva_skin', 'default': [], 'rb': 'rbRisarVulvaSkin', 'is_vector': True},
        'vulva_skin_adds': {'attr': 'vulva_skin_adds', 'default': None, 'rb': None, 'is_vector': False},
        'vulva_mucous': {'attr': 'vulva_mucous', 'default': [], 'rb': 'rbRisarMucous', 'is_vector': True},
        'vulva_mucous_adds': {'attr': 'vulva_mucous_adds', 'default': None, 'rb': None, 'is_vector': False},
        'vulva_germination': {'attr': 'vulva_germination', 'default': None,
                              'rb': 'rbRisarVulvaGermination', 'is_vector': False},
        'urethra': {'attr': 'urethra', 'default': None, 'rb': 'rbRisarUrethra', 'is_vector': False},
        'urethra_adds': {'attr': 'urethra_adds', 'default': None, 'rb': None, 'is_vector': False},
        'perianal_zona': {'attr': 'perianal_zona', 'default': [], 'rb': 'rbRisarPerianalZona', 'is_vector': True},
        'vulva_discharge_consistency': {'attr': 'vulva_discharge_consistency', 'default': [],
                                        'rb': 'rbRisarDischargeConsistency', 'is_vector': True},
        'vulva_discharge_colour': {'attr': 'vulva_discharge_colour', 'default': None,
                                   'rb': 'rbRisarDischargeColour', 'is_vector': False},
        'vulva_discharge_quantity': {'attr': 'vulva_discharge_quantity', 'default': None,
                                     'rb': 'rbRisarDischargeQuantity', 'is_vector': False},
        'vulva_discharge_smell': {'attr': 'vulva_discharge_smell', 'default': None,
                                  'rb': 'rbRisarDischargeSmell', 'is_vector': False},
        'vulva_comments': {'attr': 'vulva_comments', 'default': None, 'rb': None, 'is_vector': False},
    }

    MIRRORS_MAP = {
        'vagina_mirrors_mirrors': {'attr': 'vagina_mirrors_mirrors', 'default': None,
                                   'rb': 'rbRisarVaginaGenVisit', 'is_vector': False},
        'vagina_mirrors_adds': {'attr': 'vagina_mirrors_adds', 'default': None, 'rb': None, 'is_vector': False},
        'vagina_paries_mirrors': {'attr': 'vagina_paries_mirrors', 'default': None,
                                  'rb': 'rbRisarVaginaParies', 'is_vector': False},
        'vagina_paries_mirrors_other': {'attr': 'vagina_paries_mirrors_other', 'default': None,
                                        'rb': None, 'is_vector': False},
        'cervix_uteri_mirrors': {'attr': 'cervix_uteri_mirrors', 'default': None,
                                 'rb': 'rbRisarCervixUteri', 'is_vector': False},
        'cervix_uteri_size_mirrors': {'attr': 'cervix_uteri_size_mirrors', 'default': None,
                                      'rb': 'rbRisarCervixUteriSize', 'is_vector': False},
        'cervix_uteri_shape_mirrors': {'attr': 'cervix_uteri_shape_mirrors', 'default': None,
                                       'rb': 'rbRisarCervixUteriShape', 'is_vector': False},
        'anabrosis_mirrors': {'attr': 'anabrosis_mirrors', 'default': None, 'rb': None, 'is_vector': False},
        'ectropion_mirrors': {'attr': 'ectropion_mirrors', 'default': None, 'rb': None, 'is_vector': False},
        'uterus_external_orifice_mirrors': {'attr': 'uterus_external_orifice_mirrors', 'default': None,
                                            'rb': 'rbRisarUterusExternalOrifice', 'is_vector': False},
        'vaginal_fornix_mirrors': {'attr': 'vaginal_fornix_mirrors', 'default': [],
                                   'rb': 'rbRisarVaginalFornix', 'is_vector': True},
        'vaginal_fornix_adds_mirrors': {'attr': 'vaginal_fornix_adds_mirrors', 'default': None,
                                        'rb': None, 'is_vector': False},
        'discharge_consistency_mirrors': {'attr': 'discharge_consistency_mirrors', 'default': [],
                                          'rb': 'rbRisarDischargeConsistency', 'is_vector': True},
        'discharge_colour_mirrors': {'attr': 'discharge_colour_mirrors', 'default': None,
                                     'rb': 'rbRisarDischargeColour', 'is_vector': False},
        'discharge_quantity_mirrors': {'attr': 'discharge_quantity_mirrors', 'default': None,
                                       'rb': 'rbRisarDischargeQuantity', 'is_vector': False},
        'discharge_smell_mirrors': {'attr': 'discharge_smell_mirrors', 'default': None,
                                    'rb': 'rbRisarDischargeSmell', 'is_vector': False},
        'comments_mirrors': {'attr': 'comments_mirrors', 'default': None, 'rb': None, 'is_vector': False},
    }

    BIMANUAL_MAP = {
        'bimanual_cervix_uteri': {'attr': 'bimanual_cervix_uteri', 'default': None,
                                  'rb': 'rbRisarCervixUteri', 'is_vector': False},
        'bimanual_cervix_consistency': {'attr': 'bimanual_cervix_consistency', 'default': None,
                                        'rb': 'rbRisarCervix_Consistency', 'is_vector': False},
        'bimanual_uterus_body': {'attr': 'bimanual_uterus_body', 'default': [],
                                 'rb': 'rbRisarUterusBodyGenVisit', 'is_vector': True},
        'bimanual_body_of_womb_size': {'attr': 'bimanual_body_of_womb_size', 'default': None,
                                       'rb': 'rbRisarBody_Of_Womb_Size', 'is_vector': False},
        'bimanual_body_of_womb_enlarged': {'attr': 'bimanual_body_of_womb_enlarged', 'default': None,
                                           'rb': None, 'is_vector': False},
        'bimanual_uteri_position': {'attr': 'bimanual_uteri_position', 'default': [],
                                    'rb': 'rbRisarUteriPositionGenVisit', 'is_vector': True},
        'bimanual_ovary_right': {'attr': 'bimanual_ovary_right', 'default': [],
                                 'rb': 'rbRisarOvary', 'is_vector': True},
        'bimanual_ovary_right_oher': {'attr': 'bimanual_ovary_right_oher', 'default': None,
                                      'rb': None, 'is_vector': False},
        'bimanual_ovary_left': {'attr': 'bimanual_ovary_left', 'default': [],
                                'rb': 'rbRisarOvary', 'is_vector': True},
        'bimanual_ovary_left_oher': {'attr': 'bimanual_ovary_left_oher', 'default': None,
                                     'rb': None, 'is_vector': False},
        'bimanual_uterine_tubes_right': {'attr': 'bimanual_uterine_tubes_right', 'default': None,
                                         'rb': None, 'is_vector': False},
        'bimanual_uterine_tubes_left': {'attr': 'bimanual_uterine_tubes_left', 'default': None,
                                        'rb': None, 'is_vector': False},
        'bimanual_vaginal_fornix': {'attr': 'bimanual_vaginal_fornix', 'default': [],
                                    'rb': 'rbRisarVaginalFornix', 'is_vector': True},
        'bimanual_comments': {'attr': 'bimanual_comments', 'default': None,
                              'rb': None, 'is_vector': False},
    }

    RECTOVAGINAL_MAP = {
        'rectovaginal_cervix_uteri': {'attr': 'rectovaginal_cervix_uteri', 'default': None,
                                      'rb': 'rbRisarCervixUteri', 'is_vector': False},
        'rectovaginal_cervix_consistency': {'attr': 'rectovaginal_cervix_consistency', 'default': None,
                                            'rb': 'rbRisarCervix_Consistency', 'is_vector': False},
        'rectovaginal_uterus_body': {'attr': 'rectovaginal_uterus_body', 'default': [],
                                     'rb': 'rbRisarUterusBodyGenVisit', 'is_vector': True},
        'rectovaginal_body_of_womb_size': {'attr': 'rectovaginal_body_of_womb_size', 'default': None,
                                           'rb': 'rbRisarBody_Of_Womb_Size', 'is_vector': False},
        'rectovaginal_body_of_womb_enlarged': {'attr': 'rectovaginal_body_of_womb_enlarged', 'default': None,
                                               'rb': None, 'is_vector': False},
        'rectovaginal_uteri_position': {'attr': 'rectovaginal_uteri_position', 'default': [],
                                        'rb': 'rbRisarUteriPositionGenVisit', 'is_vector': True},
        'rectovaginal_parametrium': {'attr': 'rectovaginal_parametrium', 'default': [],
                                     'rb': 'rbRisarParametrium1', 'is_vector': True},
        'rectovaginal_parametrium_other': {'attr': 'rectovaginal_parametrium_other', 'default': None,
                                           'rb': None, 'is_vector': False},
        'rectovaginal_ovary_right': {'attr': 'rectovaginal_ovary_right', 'default': [],
                                     'rb': 'rbRisarOvary', 'is_vector': True},
        'rectovaginal_ovary_right_oher': {'attr': 'rectovaginal_ovary_right_oher', 'default': None,
                                          'rb': None, 'is_vector': False},
        'rectovaginal_ovary_left': {'attr': 'rectovaginal_ovary_left', 'default': [],
                                    'rb': 'rbRisarOvary', 'is_vector': True},
        'rectovaginal_ovary_left_oher': {'attr': 'rectovaginal_ovary_left_oher', 'default': None,
                                         'rb': None, 'is_vector': False},
        'rectovaginal_uterine_tubes_right': {'attr': 'rectovaginal_uterine_tubes_right', 'default': None,
                                             'rb': None, 'is_vector': False},
        'rectovaginal_uterine_tubes_left': {'attr': 'rectovaginal_uterine_tubes_left', 'default': None,
                                            'rb': None, 'is_vector': False},
        'rectovaginal_vaginal_fornix': {'attr': 'rectovaginal_vaginal_fornix', 'default': [],
                                        'rb': 'rbRisarVaginalFornix', 'is_vector': True},
        'rectovaginal_comments': {'attr': 'rectovaginal_comments', 'default': None,
                                  'rb': None, 'is_vector': False},
    }

    RECTAL_MAP = {
        'rectal_perianal_zona': {'attr': 'rectal_perianal_zona', 'default': [],
                                 'rb': 'rbRisarPerianalZona', 'is_vector': True},
        'rectal_rectum': {'attr': 'rectal_rectum', 'default': [],
                          'rb': 'rbRisarRectum', 'is_vector': True},
        'rectal_cervix_uteri': {'attr': 'rectal_cervix_uteri', 'default': None,
                                'rb': 'rbRisarCervixUteri', 'is_vector': False},
        'rectal_cervix_consistency': {'attr': 'rectal_cervix_consistency', 'default': None,
                                      'rb': 'rbRisarCervix_Consistency', 'is_vector': False},
        'rectal_uterus_body': {'attr': 'rectal_uterus_body', 'default': [],
                               'rb': 'rbRisarUterusBodyGenVisit', 'is_vector': True},
        'rectal_body_of_womb_size': {'attr': 'rectal_body_of_womb_size', 'default': None,
                                     'rb': 'rbRisarBody_Of_Womb_Size', 'is_vector': False},
        'rectal_body_of_womb_enlarged': {'attr': 'rectal_body_of_womb_enlarged', 'default': None,
                                         'rb': None, 'is_vector': False},
        'rectal_uteri_position': {'attr': 'rectal_uteri_position', 'default': [],
                                  'rb': 'rbRisarUteriPositionGenVisit', 'is_vector': True},
        'rectal_parametrium': {'attr': 'rectal_parametrium', 'default': [],
                               'rb': 'rbRisarParametrium1', 'is_vector': True},
        'rectal_parametrium_other': {'attr': 'rectal_parametrium_other', 'default': None,
                                     'rb': None, 'is_vector': False},
        'rectal_ovary_right': {'attr': 'rectal_ovary_right', 'default': [],
                               'rb': 'rbRisarOvary', 'is_vector': True},
        'rectal_ovary_right_oher': {'attr': 'rectal_ovary_right_oher', 'default': None,
                                    'rb': None, 'is_vector': False},
        'rectal_ovary_left': {'attr': 'rectal_ovary_left', 'default': [],
                              'rb': 'rbRisarOvary', 'is_vector': True},
        'rectal_ovary_left_oher': {'attr': 'rectal_ovary_left_oher', 'default': None,
                                   'rb': None, 'is_vector': False},
        'rectal_uterine_tubes_right': {'attr': 'rectal_uterine_tubes_right', 'default': None,
                                       'rb': None, 'is_vector': False},
        'rectal_uterine_tubes_left': {'attr': 'rectal_uterine_tubes_left', 'default': None,
                                      'rb': None, 'is_vector': False},
        'rectal_vaginal_fornix': {'attr': 'rectal_vaginal_fornix', 'default': [],
                                  'rb': 'rbRisarVaginalFornix', 'is_vector': True},
        'rectal_comments': {'attr': 'rectal_comments', 'default': None,
                            'rb': None, 'is_vector': False},
    }

    REPORT_MAP = {
        'encompassing_comments': {'attr': 'encompassing_comments', 'default': None, 'rb': None, 'is_vector': False},
        'encompassing_treatment': {'attr': 'encompassing_treatment', 'default': None, 'rb': None, 'is_vector': False},
        'treatment_recommendations': {'attr': 'treatment_recommendations', 'default': None, 'rb': None, 'is_vector': False},
    }

    DIAG_KINDS_MAP = {
        'main': {'attr': 'diagnosis_osn', 'default': None, 'is_vector': False, 'level': 1},
        'complication': {'attr': 'diagnosis_osl', 'default': [], 'is_vector': True, 'level': 2},
        'associated': {'attr': 'diagnosis_sop', 'default': [], 'is_vector': True, 'level': 3},
    }

    def _find_target_obj_query(self):
        res = self.target_obj_class.query.join(ActionType).filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.deleted == 0,
            ActionType.flatCode == risar_gyn_checkup_flat_code,
        )
        if self.target_obj_id:
            res = res.filter(self.target_obj_class.id == self.target_obj_id,)
        return res

    def update_target_obj(self, data):
        self.find_parent_obj(self.parent_obj_id)
        self.set_pcard()
        self.target_obj = get_action_by_id(self.target_obj_id, self.parent_obj, risar_gyn_checkup_flat_code, True)
        form_data = self.mapping_as_form(data)
        self.update_form(form_data)
        self.save_external_data()

    def mapping_as_form(self, data):
        res = {}
        self.mapping_general_info(data, res)
        self.mapping_objective(data, res)
        self.mapping_vulva(data, res)
        self.mapping_mirrors(data, res)
        self.mapping_bimanual(data, res)
        self.mapping_rectovaginal(data, res)
        self.mapping_rectal(data, res)
        self.mapping_medical_report(data, res)
        return res

    def mapping_general_info(self, data, res):
        gi = data.get('general_info', {})
        self.mapping_part(self.GENERAL_MAP, gi, res)
        res['person'] = self.find_doctor(data.get('doctor'), data.get('hospital'))
        res['beg_date'] = safe_datetime(safe_date(data['date']))

    def mapping_objective(self, data, res):
        o = data.get('objective', {})
        self.mapping_part(self.OBJECTIVE_MAP, o, res)

    def mapping_vulva(self, data, res):
        v = data.get('vulva', {})
        self.mapping_part(self.VULVA_MAP, v, res)

    def mapping_mirrors(self, data, res):
        m = data.get('mirrors', {})
        self.mapping_part(self.MIRRORS_MAP, m, res)

    def mapping_bimanual(self, data, res):
        b = data.get('bimanual', {})
        self.mapping_part(self.BIMANUAL_MAP, b, res)

    def mapping_rectovaginal(self, data, res):
        r = data.get('rectovaginal', {})
        self.mapping_part(self.RECTOVAGINAL_MAP, r, res)

    def mapping_rectal(self, data, res):
        r = data.get('rectal', {})
        self.mapping_part(self.RECTAL_MAP, r, res)

    def mapping_medical_report(self, data, res):
        mr = data.get('medical_report', {})
        self.mapping_part(self.REPORT_MAP, mr, res)

        diag_data = []
        if 'diagnosis_osn' in mr:
            diag_data.append({
                'kind': 'main',
                'mkbs': [mr['diagnosis_osn']]
            })
        if 'diagnosis_osl' in mr:
            diag_data.append({
                'kind': 'complication',
                'mkbs': mr['diagnosis_osl']
            })
        if 'diagnosis_sop' in mr:
            diag_data.append({
                'kind': 'associated',
                'mkbs': mr['diagnosis_sop']
            })
        old_action_data = {
            'begDate': self.target_obj.begDate,
            'endDate': self.target_obj.endDate,
            'person': self.target_obj.person
        }
        res.update({
            '_data_for_diags': {
                'diags_list': [
                    {
                        'diag_data': diag_data,
                        'diag_type': 'final'
                    }
                ],
                'old_action_data': old_action_data
            }
        })

    def update_form(self, data):
        # like blueprints.risar.views.api.checkups.api_0_pregnancy_checkup

        beg_date = data['beg_date']
        person = data.get('person')
        data_for_diags = data.pop('_data_for_diags')

        action = self.target_obj

        action.begDate = beg_date
        action.setPerson = person
        action.person = person
        self.ais.refresh(self.target_obj)
        self.ais.set_cur_enddate()

        for code, value in data.iteritems():
            if code in action.propsByCode:
                action.propsByCode[code].value = value

        self.update_diagnoses_system(data_for_diags['diags_list'], data_for_diags['old_action_data'])

        self.ais.close_previous()

    def delete_target_obj(self):
        self.find_parent_obj(self.parent_obj_id)
        self.target_obj = get_action_by_id(self.target_obj_id, self.parent_obj, risar_gyn_checkup_flat_code, True)
        self.ais.refresh(self.target_obj)
        self.delete_diagnoses()

        self.target_obj_class.query.filter(
            self.target_obj_class.event_id == self.parent_obj_id,
            self.target_obj_class.id == self.target_obj_id,
            Action.deleted == 0
        ).update({'deleted': 1})

        self.delete_external_data()

        # todo: при удалении последнего осмотра наверно нужно открывать предпослений
        # if self.ais.left: ...

    def as_json(self):
        data = represent_gyn_checkup(self.target_obj)
        person = data.get('person')
        return {
            "exam_gyn_id": self.target_obj.id,
            "external_id": self.external_id,
            'date': self.target_obj.begDate,
            'hospital': self.from_org_rb(person.organisation) if person else None,
            'doctor': self.from_person_rb(person),
            "general_info": self._represent_general_info(data),
            "objective": self._represent_objective(data),
            "vulva": self._represent_vulva(data),
            "mirrors": self._represent_mirrors(data),
            "bimanual": self._represent_bimanual(data),
            "rectovaginal": self._represent_rectovaginal(data),
            "rectal": self._represent_rectal(data),
            "medical_report": self._represent_medical_report(data),
        }

    def _represent_general_info(self, data):
        res = self._represent_part(self.GENERAL_MAP, data)
        return res

    def _represent_objective(self, data):
        return self._represent_part(self.OBJECTIVE_MAP, data)

    def _represent_vulva(self, data):
        return self._represent_part(self.VULVA_MAP, data)

    def _represent_mirrors(self, data):
        return self._represent_part(self.MIRRORS_MAP, data)

    def _represent_bimanual(self, data):
        return self._represent_part(self.BIMANUAL_MAP, data)

    def _represent_rectovaginal(self, data):
        return self._represent_part(self.RECTOVAGINAL_MAP, data)

    def _represent_rectal(self, data):
        return self._represent_part(self.RECTAL_MAP, data)

    def _represent_medical_report(self, data):
        res = self._represent_part(self.REPORT_MAP, data)

        diags_data = data.get('diagnoses')
        for dd in diags_data:
            kind = self.DIAG_KINDS_MAP[dd['diagnosis_types']['final'].code]
            mkb_code = dd['diagnostic']['mkb'].regionalCode
            if kind['is_vector']:
                res.setdefault(kind['attr'], []).append(mkb_code)
            else:
                res[kind['attr']] = mkb_code
        return res


class CheckupGynTicket25XForm(CheckupsTicket25XFormSchema, CheckupsTicket25XForm):

    def set_checkup_xform(self):
        self.checkup_xform = CheckupGynXForm(self.version, self.new)
