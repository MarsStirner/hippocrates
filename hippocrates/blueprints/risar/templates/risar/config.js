/**
 * Created by mmalkov on 24.09.14.
 */

WebMis20
.constant('Config', {
    url: {
        api_schedule: '{{ url_for('.api_0_schedule') }}',
        api_need_hospitalization: '{{ url_for('.api_0_need_hospitalization') }}',
        api_pregnancy_week_diagram: '{{ url_for('.api_0_pregnancy_week_diagram') }}',
        api_chart: '{{ url_for('.api_0_chart') }}',
        api_mini_chart: '{{ url_for('.api_0_mini_chart') }}',
        api_event_routing: '{{ url_for('.api_0_event_routing') }}',
        api_chart_delete: '{{ url_for('.api_0_chart_delete') }}',
        api_chart_close: '{{ url_for('.api_0_chart_close') }}{0}',
        api_attach_lpu: '{{ url_for('.api_0_attach_lpu') }}',
        api_attach_lpu_mini: '/risar/api/0/client/{0}/attach_lpu',
        api_diagnoses_save: '{{ url_for('.api_0_save_diagnoses') }}{0}',
        api_anamnesis_mother: '{{ url_for('.api_0_chart') }}{0}/mother',
        api_anamnesis_father: '{{ url_for('.api_0_chart') }}{0}/father',
        api_anamnesis_pregnancies: '{{ url_for('.api_0_pregnancies_get') }}',
        api_anamnesis_transfusions: '{{ url_for('.api_0_transfusions_get') }}',
        api_anamnesis_intolerances: '{{ url_for('.api_0_intolerances_get') }}',
        api_epicrisis:'{{ url_for('.api_0_chart')}}{0}/epicrisis',
        api_newborn_inspection: '{{ url_for('.api_0_newborn_inspection_delete') }}{0}',
        api_event_search: '{{ url_for('.api_0_event_search') }}',
        api_event_search_ambulance: '{{ url_for('.api_0_event_search_ambulance') }}',
        api_event_search_area_list: '{{ url_for('.api_0_area_list') }}',
        api_event_search_area_lpu_list: '{{ url_for('.api_0_area_lpu_list') }}',
        api_event_search_lpu_doctors_list: '{{ url_for('.api_0_lpu_doctors_list') }}',
        api_current_stats: '{{ url_for('.api_0_current_stats') }}',
        api_recent_charts: '{{ url_for('.api_0_recent_charts') }}',
        api_prenatal_risk_stats: '{{ url_for('.api_0_prenatal_risk_stats') }}',
        api_death_stats: '{{ url_for('.api_0_death_stats') }}',
        api_pregnancy_final_stats: '{{ url_for('.api_0_pregnancy_final_stats') }}',
        api_measure_generate: '{{ url_for('.api_0_measure_generate') }}',
        chart_html: '{{ url_for('.html_chart') }}',
        index_html: '{{ url_for('.index_html') }}',
        inpection_edit_html:'{{ url_for('.html_inspection_edit') }}',
        ambulance_patient_info: '{{ url_for('.html_ambulance_patient_info') }}',
        api_chart_measure_list: '{{ url_for('.api_0_chart_measure_list') }}',
        api_measure_list: '{{ url_for('.api_0_measure_list') }}',
        api_chart_header: '{{ url_for('.api_0_chart_header') }}',
        api_checkup_list: '{{ url_for('.api_0_checkup_list') }}',
        api_checkup_get: '{{ url_for('.api_0_checkup_get') }}{0}',
        api_checkup_new: '{{ url_for('.api_0_checkup_new') }}{0}',
        api_checkup_save: '{{ url_for('.api_0_checkup') }}{0}',
        api_gravidograma: '{{ url_for('.api_0_gravidograma') }}',
        api_obcl_org_count_get: '{{ url_for('.api_0_obcl_org_count_get') }}',
        api_obcl_org_patient_count_get: '{{ url_for('.api_0_obcl_org_patient_count_get') }}{0}'
    }
})
;