/**
 * Created by mmalkov on 24.09.14.
 */

WebMis20
.constant('Config', {
    url: {
        api_schedule: '{{ url_for('.api_0_schedule') }}',
        api_chart: '{{ url_for('.api_0_chart') }}',
        api_chart_delete: '{{ url_for('.api_0_chart_delete') }}',
        api_checkup_save: '{{ url_for('.api_0_checkup') }}{0}',
        api_anamnesis_mother: '{{ url_for('.api_0_chart') }}{0}/mother',
        api_anamnesis_father: '{{ url_for('.api_0_chart') }}{0}/father',
        api_anamnesis_pregnancies: '{{ url_for('.api_0_pregnancies_get') }}',
        api_anamnesis_transfusions: '{{ url_for('.api_0_transfusions_get') }}',
        api_anamnesis_intolerances: '{{ url_for('.api_0_intolerances_get') }}',
        chart_html: '{{ url_for('.html_chart') }}',
        index_html: '{{ url_for('.index_html') }}',
        inpection_edit_html:'{{ url_for('.html_inspection_edit') }}'
    }
})
;