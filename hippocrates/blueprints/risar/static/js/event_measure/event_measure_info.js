'use strict';

WebMis20.service('EMModalService', ['$modal', function ($modal) {
    return {
        openView: function (event_measure, options) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/event_measure_view.html',
                size: 'lg',
                controller: EventMeasureModalCtrl,
                resolve: {
                    event_measure: function () {
                        return event_measure;
                    },
                    options: function () {
                        return options;
                    }
                }
            });
            return instance.result;
        },
        openCreate: function (event_id, checkup, event) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/em_create_list.html',
                controller: EMCreateListModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    event_id: function () {
                        return event_id
                    },
                    checkup: function () {
                        return checkup
                    },
                    event: function () {
                        return event
                    }
                }
            });
            return instance.result;
        },
        openAppointmentEdit: function (em, appointment) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/em_appointment_edit.html',
                controller: EMAppointmentModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    event_measure: function () {
                        return em
                    },
                    appointment: function () {
                        return appointment;
                    }
                }
            });
            return instance.result;
        },
        openEmResultEdit: function (em, em_result) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/em_result_edit.html',
                controller: EMResultModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    event_measure: function () {
                        return em
                    },
                    em_result: function () {
                        return em_result;
                    }
                }
            });
            return instance.result;
        }
    }
}]);

WebMis20.service('EventMeasureService', ['RisarApi', function (RisarApi) {
    this.get = function (em_id, args) {
        return RisarApi.measure.get(em_id, args);
    };
    this.save_em_list = function (event_id, data) {
        return RisarApi.measure.save_list(event_id, data);
    };
    this.execute = function (em) {
        return RisarApi.measure.execute(em.id);
    };
    this.cancel = function (em) {
        return RisarApi.measure.cancel(em.id);
    };
    this.del = function (em) {
        return RisarApi.measure.del(em.id);
    };
    this.restore = function (em) {
        return RisarApi.measure.restore(em.id);
    };
    this.new_appointment = function (em, checkup, header) {
        var start_date = moment(em.data.beg_datetime).format('YYYY-MM-DD');
        return RisarApi.measure.new_appointment(header.client.id, checkup.person.id, start_date);
    };
    this.get_appointment = function (em, checkup_id) {
        return RisarApi.measure.get_appointment(em.data.id, em.data.appointment_action_id, {
            checkup_id: checkup_id
        });
    };
    this.get_em_result = function (em) {
        return RisarApi.measure.get_em_result(em.data.id, em.data.result_action_id);
    };
    this.save_appointment_list = function (action_id, em_id_list) {
        return RisarApi.measure.save_appointment_list(action_id, em_id_list);
    };
}]);

WebMis20.directive('eventMeasureStatus', [function () {
    return {
        restrict: 'E',
        scope: {
            status: '='
        },
        template:
'<span class="label" ng-class="getClass()">[[ status.name ]]</span>',
        link: function (scope, elem, attrs) {
            scope.getClass = function () {
                var text = 'measure-status-{0}'.format(scope.status.code);
                return text;
            };
        }
    }
}]);