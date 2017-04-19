'use strict';

WebMis20.service('EventModalService', ['$modal', '$templateCache', 'WMConfig', 'WebMisApi',
        function ($modal, $templateCache, WMConfig, WebMisApi) {
    return {
        openEditHospitalisation: function (hosp_event) {
            var tUrl = WMConfig.url.event.html.modal_edit_hosp;
            //$templateCache.remove();
            var instance = $modal.open({
                templateUrl: tUrl,
                controller: EventHospModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    event: function () {
                        return hosp_event;
                    }
                }
            });
            return instance.result;
        },
        openNewHospitalisation: function (client_id) {
            var self = this;
            return WebMisApi.event.get_new_hosp(client_id)
                .then(function (hosp_event) {
                    return self.openEditHospitalisation(hosp_event);
                });
        }
    }
}]);
