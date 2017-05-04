'use strict';

WebMis20.service('EventModalService', ['$modal', '$templateCache', 'WMConfig',
        'WMEventService', function ($modal, $templateCache, WMConfig, WMEventService) {
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
            // size: 'lg',
            // windowClass: 'modal-scrollable',
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
                hosp_beds_selectable: hosp_beds_selectable || true
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
                WMEventService.get_moving(latest_moving_id),
                is_final_moving ?
                    WMEventService.get_new_moving(event_id, undefined, latest_moving_id) :
                    $q.reject()
            ])
                .then(function (current_moving, next_moving) {
                    return _openTransferModal(current_moving, next_moving, options);
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
            event: wmevent.info,
            received: wmevent.received,
            request_type_kind: wmevent.request_type_kind
        }
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
    this.get_moving = function (event_id, moving_id) {
        return WebMisApi.event.get_moving(event_id, moving_id);
    };
}]);
