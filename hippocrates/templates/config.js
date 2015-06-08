/**
 * Created by mmalkov on 12.02.15.
 */
'use strict';
angular.module('hitsl.ui')
.config([
    '$interpolateProvider', 'datepickerConfig', 'datepickerPopupConfig', 'paginationConfig', '$provide', '$tooltipProvider',
    function ($interpolateProvider, datepickerConfig, datepickerPopupConfig, paginationConfig, $provide, $tooltipProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
    datepickerConfig.showWeek = false;
    datepickerConfig.startingDay = 1;
    datepickerPopupConfig.currentText = 'Сегодня';
    datepickerPopupConfig.toggleWeeksText = 'Недели';
    datepickerPopupConfig.clearText = 'Убрать';
    datepickerPopupConfig.closeText = 'Готово';
    paginationConfig.firstText = 'Первая';
    paginationConfig.lastText = 'Последняя';
    paginationConfig.previousText = 'Предыдущая';
    paginationConfig.nextText = 'Следующая';
    $tooltipProvider.setTriggers({
        'mouseenter': 'mouseleave',
        'click': 'click',
        'focus': 'blur',
        'never': 'mouseleave',
        'show_popover': 'hide_popover'
    });
    // Workaround for bug #1404
    // https://github.com/angular/angular.js/issues/1404
    // Source: http://plnkr.co/edit/hSMzWC?p=preview
    $provide.decorator('ngModelDirective', ['$delegate', function($delegate) {
        var ngModel = $delegate[0], controller = ngModel.controller;
        ngModel.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
            var $interpolate = $injector.get('$interpolate');
            attrs.$set('name', $interpolate(attrs.name || '')(scope));
            $injector.invoke(controller, this, {
                '$scope': scope,
                '$element': element,
                '$attrs': attrs
            });
        }];
        return $delegate;
    }]);
    $provide.decorator('formDirective', ['$delegate', function($delegate) {
        var form = $delegate[0], controller = form.controller;
        form.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
            var $interpolate = $injector.get('$interpolate');
            attrs.$set('name', $interpolate(attrs.name || attrs.ngForm || '')(scope));
            $injector.invoke(controller, this, {
                '$scope': scope,
                '$element': element,
                '$attrs': attrs
            });
        }];
        return $delegate;
    }]);
}])
.constant('WMConfig', {
    url: {
        // common
        logout: '{{ url_for("logout") }}',
        doctor_to_assist: '{{ url_for("doctor_to_assist") }}',
        // patient
        api_patient_file_attach: '{{ url_for("patients.api_patient_file_attach") }}',
        api_patient_file_attach_save: '{{ url_for("patients.api_patient_file_attach_save") }}',
        api_patient_file_attach_delete: '{{ url_for("patients.api_patient_file_attach_delete") }}',
        // event
        api_event_actions: '{{ url_for("event.api_event_actions") }}',
        // external
        coldstar: {
            cas_check_token: '{{ config.COLDSTAR_URL + "cas/api/check/" }}',
            cas_prolong_token: '{{ config.COLDSTAR_URL + "cas/api/prolong/" }}',
            cas_release_token: '{{ config.COLDSTAR_URL + "cas/api/release/" }}',
            scan_get_device_list: '{{ config.COLDSTAR_URL + "scan/list/" }}',
            scan_process_scan: '{{ config.COLDSTAR_URL + "scan/scan" }}',
            ezekiel_acquire_lock: '{{ config.COLDSTAR_URL + "ezekiel/acquire/{0}" }}',
            ezekiel_prolong_lock: '{{ config.COLDSTAR_URL + "ezekiel/prolong/{0}" }}',
            ezekiel_release_lock: '{{ config.COLDSTAR_URL + "ezekiel/release/{0}" }}'
        }
    },
    settings: {
        user_idle_timeout: {{ settings.getInt('Auth.UserIdleTimeout', 15 * 60) }},
        logout_warning_timeout: {{ settings.getInt('Auth.LogoutWarningTimeout', 200) }}
    }
})
;
