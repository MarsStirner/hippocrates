'use strict';

WebMis20.service('EMModalService', ['$modal', function ($modal) {
    return {
        openView: function (event_measure) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/event_measure_view.html',
                controller: EventMeasureModalCtrl,
                //backdrop: 'static',
                //size: 'lg',
                resolve: {
                    event_measure: function () {
                        return event_measure;
                    }
                }
            });
            return instance.result;
        },
        openAppointmentEdit: function (em, appointment) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/en_appointment_edit.html',
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
        }
    }
}]);

WebMis20.service('EventMeasureService', ['RisarApi', function (RisarApi) {
    this.get = function (em_id) {
        return RisarApi.measure.get(em_id);
    };
    this.cancel = function (em) {
        return RisarApi.measure.cancel(em.id);
    };
    this.get_appointment = function (em) {
        return RisarApi.measure.get_appointment(em.data.id, em.data.appointment_action_id);
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