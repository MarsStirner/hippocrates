'use strict';

var EventMeasureActionViewCtrl = function ($scope, RisarApi, EMModalService, EventMeasureService) {
    $scope.selectAll = false;
    $scope.checkboxes = {};
    $scope.toggleSelection = function () {
        $scope.selectAll = !$scope.selectAll;
        _.map($scope.checkup.measures, function (em) {
            if ( $scope.canReadEmAppointment(em) ) {
                $scope.checkboxes[em.data.id] =  $scope.selectAll;
            }
        });
    };
    $scope.printButtonActive = function () {
        return _.any(_.values($scope.checkboxes));
    };
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
    $scope.deleteEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        EventMeasureService.del(em.data)
            .then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
    };
    $scope.restoreEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        EventMeasureService.restore(em.data)
            .then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
    };
    $scope.openEmAppointment = function (idx) {
        var em = $scope.checkup.measures[idx];
        if ($scope.canReadEmAppointment(em)) {
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
        if ($scope.canReadEmResult(em)) {
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
    $scope.addNewEventMeasures = function () {
        return EMModalService.openCreate($scope.event_id)
            .then(function () {
                RisarApi.measure.get_by_action($scope.checkup.id, {
                    with_deleted_hand_measures: true
                }).then(function (em_list) {
                    Array.prototype.splice.apply(
                        $scope.checkup.measures,
                        [0, em_list.length].concat(em_list)
                    );
                })
            });
    };
    $scope.emIsNotActual = function (em) {
        return em.data.is_actual.id === 0;
    };
    $scope.canReadEmAppointment = function (em) {
        return em.access.can_read_appointment;
    };
    $scope.canReadEmResult = function (em) {
        return em.access.can_read_result;
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
    $scope.get_ps_appointments_data = function () {
        return {
            action_id: $scope.checkup.id,
            em_id_list: $scope.getSelectedMeasuresIds()
        }
    };
    $scope.getSelectedMeasuresIds = function () {
        return _.keys(_.object(_.filter(_.pairs($scope.checkboxes),
                                                    function(item){return item[1]===true})));
    };
    $scope.createAppointments = function() {
       var em_id_list = $scope.getSelectedMeasuresIds();
        if (!_.isEmpty(em_id_list)) {
            return EventMeasureService.save_appointment_list($scope.checkup.id, em_id_list).
                then(function (em_list) {
                   _.each(em_list, function(nuevo) {
                       _.each($scope.checkup.measures, function (old, ind) {
                           if ( safe_traverse(nuevo, ['data', 'id']) === safe_traverse(old, ['data', 'id']) ) {
                               $scope.checkup.measures[ind] = nuevo;
                           };
                           });
                       });
                    return em_list;
                });
        }
    };
    $scope.canDeleteEm = function (em) {
        return em.access.can_delete;
    };
    $scope.canRestoreEm = function (em) {
        return em.access.can_restore;
    };
    $scope.isManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 0;
    };
    $scope.isDeletedManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 1;
    };
};


WebMis20.controller('EventMeasureActionViewCtrl', ['$scope', 'RisarApi', 'EMModalService', 'EventMeasureService',
    EventMeasureActionViewCtrl]);