'use strict';

WebMis20.service('EventModalService', ['$modal', '$templateCache', 'WMConfig',
        'WMEventService', function ($modal, $templateCache, WMConfig, WMEventService) {
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
                    wmevent: function () {
                        return hosp_event;
                    }
                }
            });
            return instance.result;
        },
        openNewHospitalisation: function (client_id) {
            var self = this;
            return WMEventService.get_new_hosp(client_id)
                .then(function (hosp_event) {
                    return self.openEditHospitalisation(hosp_event);
                });
        }
    }
}]);


WebMis20.service('WMEventService', ['WebMisApi', 'WMAdmissionEvent',
        function (WebMisApi, WMAdmissionEvent) {
    this.get_new_hosp = function (client_id) {
        return WebMisApi.event.get_new_hosp(client_id)
            .then(function (data) {
                var event = new WMAdmissionEvent();
                event.init_from_obj(data);
                return event;
            });
    };
    this.refresh_hosp = function (wmevent, event_id) {
        if (!wmevent.event_id) wmevent.event_id = event_id;
        return WebMisApi.event.get_hosp(wmevent.event_id)
            .then(function (data) {
                wmevent.init_from_obj(data);
                return wmevent;
            });
    };
    this.save_hosp = function (wmevent) {
        var data = {
            event: _.deepCopy(wmevent.info),
            received: wmevent.received,
            request_type_kind: wmevent.request_type_kind
        };

        data.event.client = data.event.client.info;
        return WebMisApi.event.save(data);
    };
}]);
