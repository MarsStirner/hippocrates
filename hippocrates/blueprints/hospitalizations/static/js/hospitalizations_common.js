'use strict';

WebMis20.service('HospitalizationsModalService', ['$modal', '$templateCache', 'WMConfig',
        function ($modal, $templateCache, WMConfig) {
    return {
//        openEditHospitalisation: function (hosp_event) {
//            var tUrl = WMConfig.url.event.html.modal_edit_hosp;
//            //$templateCache.remove();
//            var instance = $modal.open({
//                templateUrl: tUrl,
//                controller: EventHospModalCtrl,
//                backdrop: 'static',
//                size: 'lg',
//                windowClass: 'modal-scrollable',
//                resolve: {
//                    wmevent: function () {
//                        return hosp_event;
//                    }
//                }
//            });
//            return instance.result;
//        }
    }
}]);


WebMis20.service('HospitalizationsService', ['WebMisApi', function (WebMisApi) {
    this.get_hosp_list = function (args) {
        return WebMisApi.hospitalizations.get_list(args);
    };
    this.get_hosps_stats = function (args) {
        return WebMisApi.hospitalizations.get_stats(args);
    };
}]);
