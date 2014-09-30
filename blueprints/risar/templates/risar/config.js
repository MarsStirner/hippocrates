/**
 * Created by mmalkov on 24.09.14.
 */

WebMis20
.constant('Config', {
    url: {
        api_schedule: '{{ url_for('.api_0_schedule') }}',
        api_chart: '{{ url_for('.api_0_chart') }}',
        api_anamnesis: '{{ url_for('.api_0_anamnesis') }}',
        chart_html: '{{ url_for('.html_chart') }}'
    }
})
;