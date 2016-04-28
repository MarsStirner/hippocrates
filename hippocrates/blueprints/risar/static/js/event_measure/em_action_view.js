'use strict';

var EventMeasureActionViewCtrl = function ($scope, RisarApi, EMModalService, EventMeasureService) {
    $scope.generateMeasures = function () {
        RisarApi.measure.regenerate($scope.checkup.id).
            then(function (measures) {
                $scope.checkup.measures = measures;
            });
    };
    $scope.removeMeasures = function () {
        RisarApi.measure.remove($scope.checkup.id).
            then(function (measures) {
                $scope.checkup.measures = measures;
            });
    };
    $scope.viewEventMeasure = function (idx) {
        var em = $scope.checkup.measures[idx];
        EMModalService.openView(em.data);
    };
    $scope.executeEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        EventMeasureService.execute(em.data)
            .then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
    };
    $scope.cancelEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        EventMeasureService.cancel(em.data)
            .then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
    };
    $scope.openEmAppointment = function (idx) {
        var em = $scope.checkup.measures[idx];
        if ($scope.canEditEmAppointment(em)) {
            EventMeasureService.get_appointment(em)
                .then(function (appointment) {
                    return EMModalService.openAppointmentEdit(em, appointment);
                })
                .then(function (result) {
                    return EventMeasureService.get(em.data.id)
                        .then(function (upd_em) {
                            $scope.checkup.measures.splice(idx, 1, upd_em);
                        });
                });
        }
    };
    $scope.openEmResult = function (idx) {
        var em = $scope.checkup.measures[idx];
        if ($scope.canEditEmResult(em)) {
            EventMeasureService.get_em_result(em)
                .then(function (em_result) {
                    return EMModalService.openEmResultEdit(em, em_result);
                })
                .then(function (result) {
                    return EventMeasureService.get(em.data.id)
                        .then(function (upd_em) {
                            $scope.checkup.measures.splice(idx, 1, upd_em);
                        });
                });
        }
    };
    $scope.emIsNotActual = function (em) {
        return em.data.is_actual.id === 0;
    };
    $scope.canEditEmAppointment = function (em) {
        return em.access.can_edit_appointment;
    };
    $scope.canEditEmResult = function (em) {
        return em.access.can_edit_result;
    };
    $scope.emHasAppointment = function (em) {
        return Boolean(em.data.appointment_action_id);
    };
    $scope.emHasResult = function (em) {
        return Boolean(em.data.result_action_id);
    };
    $scope.canNewAppointment = function (em) {
        return em.data.measure.measure_type.code === 'checkup';
    };
    $scope.newAppointment = function(em, checkup, header) {
        if($scope.canNewAppointment(em)) {
            EventMeasureService.new_appointment(em, checkup, header);
        }
    };
};


WebMis20.controller('EventMeasureActionViewCtrl', ['$scope', 'RisarApi', 'EMModalService', 'EventMeasureService',
    EventMeasureActionViewCtrl]);