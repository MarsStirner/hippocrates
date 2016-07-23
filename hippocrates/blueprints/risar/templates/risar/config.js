/**
 * Created by mmalkov on 24.09.14.
 */

WebMis20
.constant('Config', {
    url: {
        gyn: {
            /* TODO: Понемногу выносить УРЛы */
            chart:'{{ url_for('.api_0_gyn_chart', event_id=-99).replace('-99', '{0}') }}',
            mini_chart: '{{ url_for('.api_0_gyn_chart_mini', event_id=-99).replace('-99', '{0}') }}',
            header: '{{ url_for('.api_0_chart_header', event_id=-99).replace('-99', '{0}') }}',
            delete: '{{ url_for('.api_0_gyn_chart_delete', ticket_id=-99).replace('-99', '{0}') }}',
            close: '{{ url_for('.api_0_gyn_chart_close', event_id=-99).replace('-99', '{0}') }}',
            anamnesis: '{{ url_for('.api_0_gyn_anamnesis', event_id=-99).replace('-99', '{0}') }}',
            anamnesis_general: '{{ url_for('.api_0_gyn_anamnesis_general', event_id=-99).replace('-99', '{0}') }}',
            checkup: '{{ url_for('.api_0_gyn_checkup_get', event_id=-99, checkup_id=-98).replace('-99', '{0}').replace('-98', '{1}') }}',
            checkup_list: '{{ url_for('.api_0_gyn_checkup_list', event_id=-99).replace('-99', '{0}') }}',
            checkup_new: '{{ url_for('.api_0_gyn_checkup_get_new', event_id=-99, flat_code='-98').replace('-99', '{0}').replace('-98', '{1}') }}',
            checkup_post: '{{ url_for('.api_0_gyn_checkup', event_id=-99).replace('-99', '{0}') }}',
        },
        api_schedule: '{{ url_for('.api_0_schedule') }}',
        api_need_hospitalization: '{{ url_for('.api_0_need_hospitalization') }}',
        api_stats_pregnancy_week_diagram: '{{ url_for('.api_1_stats_pregnancy_week_diagram') }}',
        api_chart: '{{ url_for('.api_1_pregnancy_chart', event_id=-99).replace('-99', '{0}') }}',
        api_mini_chart: '{{ url_for('.api_0_mini_chart') }}',
        api_event_routing: '{{ url_for('.api_0_event_routing') }}',
        api_chart_delete: '{{ url_for('.api_0_chart_delete') }}',
        api_chart_close: '{{ url_for('.api_0_chart_close') }}{0}',
        api_attach_lpu: '{{ url_for('.api_0_attach_lpu') }}',
        api_attach_lpu_mini: '{{ url_for('.api_0_mini_attach_lpu', client_id=-99).replace('-99', '{0}') }}',
        api_anamnesis: '{{ url_for('.api_0_pregnancy_chart') }}{0}/anamnesis',
        api_anamnesis_mother: '{{ url_for('.api_0_pregnancy_chart') }}{0}/mother',
        api_anamnesis_father: '{{ url_for('.api_0_pregnancy_chart') }}{0}/father',
        api_anamnesis_pregnancies: '{{ url_for('.api_0_pregnancies_get', action_id=-99).replace('-99', '{0}') }}',
        api_anamnesis_pregnancies_undelete: '{{ url_for('.api_0_pregnancies_undelete', action_id=-99).replace('-99', '{0}') }}',
        api_anamnesis_transfusions: '{{ url_for('.api_0_transfusions_get') }}',
        api_anamnesis_intolerances: '{{ url_for('.api_0_intolerances_get') }}',
        api_epicrisis:'{{ url_for('.api_0_pregnancy_chart')}}{0}/epicrisis',
        api_newborn_inspection: '{{ url_for('.api_0_newborn_inspection_delete') }}{0}',
        api_event_search: '{{ url_for('.api_0_event_search') }}',
        api_event_print: '{{ url_for('.api_0_event_print') }}',
        api_event_search_ambulance: '{{ url_for('.api_0_event_search_ambulance') }}',
        api_event_search_area_list: '{{ url_for('.api_0_area_list') }}',
        api_event_search_area_curator_list: '{{ url_for('.api_0_area_curator_list') }}',
        api_event_search_curator_lpu_list: '{{ url_for('.api_0_curator_lpu_list') }}',
        api_event_search_lpu_doctors_list: '{{ url_for('.api_0_lpu_doctors_list') }}',
        api_stats_current_cards_overview: '{{ url_for('.api_1_stats_current_cards_overview') }}',
        api_recent_charts: '{{ url_for('.api_0_recent_charts') }}',
        api_recently_modified_charts: '{{ url_for('.api_0_recently_modified_charts') }}',
        api_death_stats: '{{ url_for('.api_0_death_stats') }}',
        api_pregnancy_final_stats: '{{ url_for('.api_0_pregnancy_final_stats') }}',
        api_event_measure_generate: '{{ url_for('.api_0_event_measure_generate') }}',
        api_event_measure_get: '{{ url_for('.api_0_event_measure_get') }}',
        api_event_measure_remove: '{{ url_for('.api_0_event_measure_remove') }}',
        api_event_measure_execute: '{{ url_for('.api_0_event_measure_execute') }}',
        api_event_measure_cancel: '{{ url_for('.api_0_event_measure_cancel') }}',
        api_event_measure_appointment_get: '{{ url_for('.api_0_event_measure_appointment_get', event_measure_id=-90) | replace("-90", "{0}") }}',
        api_event_measure_appointment_save: '{{ url_for('.api_0_event_measure_appointment_save', event_measure_id=-90) | replace("-90", "{0}") }}',
        api_event_measure_result_get: '{{ url_for('.api_0_event_measure_result_get', event_measure_id=-90) | replace("-90", "{0}") }}',
        api_event_measure_result_save: '{{ url_for('.api_0_event_measure_result_save', event_measure_id=-90) | replace("-90", "{0}") }}',
        api_event_measure_checkups: '{{ url_for('.api_0_event_measure_checkups') }}',
        url_schedule_appointment_html: '{{ url_for('schedule.appointment') }}',
        chart_auto_html: '{{ url_for('.html_auto_chart') }}',
        chart_pregnancy_html: '{{ url_for('.html_pregnancy_chart') }}',
        chart_gynecological_html: '{{ url_for('.html_gynecological_chart') }}',
        index_html: '{{ url_for('.index_html') }}',
        anamnesis_html: '{{ url_for('.html_anamnesis') }}',
        inpection_read_html:'{{ url_for('.html_inspection_read') }}',
        inpection_edit_html:'{{ url_for('.html_inspection_edit') }}',
        inspection_pc_edit_html:'{{ url_for('.html_inspection_pc_edit') }}',
        inspection_puerpera_edit_html:'{{ url_for('.html_inspection_puerpera_edit') }}',
        epicrisis_html:'{{ url_for('.html_epicrisis') }}',
        ambulance_patient_info: '{{ url_for('.html_ambulance_patient_info') }}',
        card_fill_history: '{{ url_for('.html_card_fill_history') }}',
        api_chart_measure_list: '{{ url_for('.api_0_chart_measure_list') }}',
        api_measure_list: '{{ url_for('.api_0_measure_list') }}',
        api_chart_header: '{{ url_for('.api_0_chart_header', event_id=-90).replace('-90', '{0}') }}',
        api_checkup_list: '{{ url_for('.api_0_pregnancy_checkup_list') }}',
        api_checkup_get: '{{ url_for('.api_0_pregnancy_checkup_get') }}{0}',
        api_checkup_new: '{{ url_for('.api_0_pregnancy_checkup_new') }}{0}',
        api_checkup_save: '{{ url_for('.api_0_pregnancy_checkup') }}{0}',
        api_fetus_list: '{{ url_for('.api_0_fetus_list') }}',
        api_checkup_puerpera_list: '{{ url_for('.api_0_pregnancy_checkup_puerpera_list') }}',
        api_checkup_puerpera_get: '{{ url_for('.api_0_pregnancy_checkup_puerpera_get') }}{0}',
        api_checkup_puerpera_new: '{{ url_for('.api_0_pregnancy_checkup_puerpera_new') }}{0}',
        api_checkup_puerpera_save: '{{ url_for('.api_0_pregnancy_checkup_puerpera') }}{0}',
        api_gravidograma: '{{ url_for('.api_0_gravidograma') }}',
        api_stats_perinatal_risk_rate: '{{ url_for('.api_0_stats_perinatal_risk_rate') }}',
        api_stats_obcl_get: '{{ url_for('.api_0_stats_obcl_get') }}',
        api_stats_obcl_orgs_get: '{{ url_for('.api_0_stats_obcl_orgs_get') }}{0}',
        api_stats_org_curation_get: '{{ url_for('.api_0_stats_org_curation_get') }}',
        api_stats_urgent_errands: '{{ url_for('.api_0_stats_urgent_errands') }}',
        api_stats_doctor_card_fill_rates: '{{ url_for('.api_0_stats_doctor_card_fill_rates') }}',
        api_stats_card_fill_rates_lpu_overview: '{{ url_for('.api_0_stats_card_fill_rates_lpu_overview') }}',
        api_stats_card_fill_rates_doctor_overview: '{{ url_for('.api_0_stats_card_fill_rates_doctor_overview') }}',
        api_stats_risk_group_distribution: '{{ url_for('.api_0_stats_risk_group_distribution') }}',
        api_errands_get: '{{ url_for('.api_0_errands_get') }}',
        api_errands_summary: '{{ url_for('.api_0_errands_summary') }}',
        api_errand_get: '{{ url_for('.api_0_errand_get') }}',
        api_errand_save: '{{ url_for('.api_0_errand_save') }}',
        api_errand_mark_as_read: '{{ url_for('.api_0_errand_mark_as_read') }}{0}',
        api_errand_execute: '{{ url_for('.api_0_errand_execute') }}{0}',
        api_errand_delete: '{{ url_for('.api_0_errand_delete') }}{0}',
        api_stats_pregnancy_pathology: '{{ url_for('.api_0_stats_pregnancy_pathology') }}',
        api_chart_card_fill_history: '{{ url_for('.api_0_chart_card_fill_history') }}',
        api_chart_risk_groups_list: '{{ url_for('.api_0_chart_risks', event_id=-90) | replace("-90", "{0}") }}',
        api_concilium_list_get: '{{ url_for('.api_0_concilium_list_get', event_id=-90) | replace("-90", "{0}") }}',
        api_concilium_get: '{{ url_for('.api_0_concilium_get', event_id=-90) | replace("-90", "{0}") }}',
        api_person_contacts_get: '{{ url_for('schedule.api_person_contacts_get') }}{0}',

    }
})
;