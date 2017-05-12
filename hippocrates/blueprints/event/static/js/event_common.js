'use strict';

WebMis20.service('EventModalService', ['$modal', '$templateCache', '$q', 'WMConfig',
        'WMEventService', function ($modal, $templateCache, $q, WMConfig, WMEventService) {

    var _openHospInfoModal = function (hosp_event) {
        var tUrl = WMConfig.url.event.html.modal_hosp_info;
        //$templateCache.remove();
        var instance = $modal.open({
            templateUrl: tUrl,
            controller: EventHospInfoModalCtrl,
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
    };
    var _openMovingModal = function (moving, options) {
        var instance = $modal.open({
            templateUrl: '/WebMis20/modal/event/moving.html',
            controller: MovingModalCtrl,
            backdrop: 'static',
            size: 'lg',
            windowClass: 'modal-scrollable',
            resolve: {
                moving: function () {
                    return moving;
                },
                options: function () {
                    return options;
                }
            }
        });
        return instance.result;
    };
    var _openMovingTransferModal = function (current_moving, next_moving, options) {
        var instance = $modal.open({
            templateUrl: '/WebMis20/modal/event/moving_transfer.html',
            controller: MovingTransferModalCtrl,
            backdrop: 'static',
            resolve: {
                current_moving: function () {
                    return current_moving;
                },
                next_moving: function () {
                    return next_moving;
                },
                options: function () {
                    return options;
                }
            }
        });
        return instance.result;
    };
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
        },
        openHospitalisationInfo: function (event_id) {
            var self = this;
            return WMEventService.get_stationary_event(event_id)
                .then(function (wmevent) {
                    return _openHospInfoModal(wmevent);
                });
        },
        // при наличии поступления будет создаваться новое движение,
        // возможно с выбором койки
        openMakeMoving: function (event_id, received_id, hosp_beds_selectable) {
            var options = {
                hosp_beds_selectable: hosp_beds_selectable || false
            };
            return WMEventService.get_new_moving(event_id, received_id)
                .then(function (moving) {
                    return _openMovingModal(moving, options);
                });
        },
        // для созданного движения будет выбираться койка или просто
        // будет происходить редактирование движения
        openEditMoving: function (event_id, moving_id) {
            var options = {
                hosp_beds_selectable: true
            };
            return WMEventService.get_moving(event_id, moving_id)
                .then(function (moving) {
                    return _openMovingModal(moving, options);
                });
        },
        // для созданного движения будет выбираться отделение куда
        // будет совершен перевод, текущее движение будет закрываться,
        // следующее движение будет создано (если ИБ продолжается,
        // иначе - текущее движение будет последним)
        openMakeTransfer: function (event_id, latest_moving_id, is_final_moving) {
            var options = {
                is_final_moving: is_final_moving || false
            };
            return $q.all([
                WMEventService.get_moving(event_id, latest_moving_id),
                is_final_moving ?
                    $q.when() :
                    WMEventService.get_new_moving(event_id, undefined, latest_moving_id)
            ])
                .then(function (movings) {
                    var current_moving = movings[0],
                        next_moving = movings[1];
                    return _openMovingTransferModal(current_moving, next_moving, options);
                });
        }
    }
}]);


WebMis20.service('WMEventService', ['WebMisApi', 'WMAdmissionEvent', 'WMStationaryEvent',
        function (WebMisApi, WMAdmissionEvent, WMStationaryEvent) {
    this.get_new_hosp = function (client_id) {
        return WebMisApi.event.get_new_hosp(client_id)
            .then(function (data) {
                var event = new WMAdmissionEvent();
                event.init_from_obj(data);
                return event;
            });
    };
    this.get_hosp = function (event_id) {
        return WebMisApi.event.get_hosp(event_id)
            .then(function (data) {
                var event = new WMAdmissionEvent();
                event.init_from_obj(data);
                return event;
            });
    };
    this.get_stationary_event = function (event_id) {
        return WebMisApi.event.get(event_id)
            .then(function (data) {
                var event = new WMStationaryEvent();
                event.init_from_obj({result: data});
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
            event: wmevent.info,
            received: wmevent.received,
            request_type_kind: wmevent.request_type_kind
        };
        data.event.client = data.event.client.info;
        return WebMisApi.event.save(data);
    };
    this.get_new_moving = function (event_id, received_id, latest_moving_id) {
        return WebMisApi.event.get_moving(event_id, undefined, {
            received_id: received_id,
            latest_moving_id: latest_moving_id,
            new: true
        });
    };
    this.get_movings = function (event_id) {
        return WebMisApi.event.get_movings(event_id);
    };
    this.get_moving = function (event_id, moving_id) {
        return WebMisApi.event.get_moving(event_id, moving_id);
    };
    this.save_moving = function (moving) {
        var moving_id = moving.id,
            event_id = moving.event_id;
        return WebMisApi.event.save_moving(event_id, moving_id, moving);
    };
    this.get_available_hosp_beds = function (org_struct_id, selected_hb_id) {
        var args = {
            org_str_id : org_struct_id,
            hb_id: selected_hb_id
        };
        return WebMisApi.event.get_available_hosp_beds(args);
    };
}]);
