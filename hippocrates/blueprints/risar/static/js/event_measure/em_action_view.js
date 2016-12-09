'use strict';

var EventMeasureActionViewCtrl = function ($scope, $q, RisarApi, EMModalService, EventMeasureService,
        RefBookService) {
    $scope.checkboxes = {};
    var viewMode = 'grouped';
    var cancelled_statuses = ['cancelled', 'cancelled_invalid', 'cancelled_dupl',
        'cancelled_changed_data', 'overdue'];

    $scope.setViewMode = function (vm) {
        viewMode = vm;
    };
    $scope.isGroupedView = function () {
        return viewMode === 'grouped';
    };
    $scope.isListedView = function () {
        return viewMode === 'listed';
    };

    $scope.toggleSelection = function () {
        var enabled = !$scope.checkSelectedAll();
        _.map($scope.checkup.measures, function (em) {
            if ($scope.canSelectEMAppointment(em)) {
                $scope.checkboxes[em.data.id] = enabled;
            }
        });
    };
    $scope.toggleByGroup = function (group) {
        var enabled = !$scope.checkSelectedAll(group);
        angular.forEach($scope.grouped[group], function (obj, status) {
            $scope.toggleByStatus(group, status, enabled);
        });
    };
    $scope.toggleByStatus = function (group, status, enabled) {
        var enabled = enabled !== undefined ?
            enabled :
            !$scope.checkSelectedByStatus(group, status);
        angular.forEach($scope.grouped[group][status], function (list, mcode) {
            $scope.toggleByMeasure(group, status, mcode, enabled);
        });
    };
    $scope.toggleByMeasure = function (group, status, mcode, enabled) {
        var enabled = enabled !== undefined ?
            enabled :
            !$scope.checkSelectedByMeasure (group, status, mcode);
        $scope.grouped[group][status][mcode].forEach(function (em) {
            if ($scope.canSelectEMAppointment(em)) {
                $scope.checkboxes[em.data.id] = enabled;
            }
        });
    };
    $scope.checkSelectedByStatus = function (group, status) {
        var mcodes = $scope.grouped[group] && _.keys($scope.grouped[group][status]);
        return mcodes && (
            mcodes.every(function (mcode) {
                return (
                    // can't be selected at all
                    !$scope.canSelectMeasureGroup(group, status, mcode) ||
                    // or all selected
                    $scope.checkSelectedByMeasure(group, status, mcode)
                );
            })
        );
    };
    $scope.checkSelectedByMeasure = function (group, status, mcode) {
        return $scope.grouped[group] &&
            $scope.grouped[group][status][mcode].every(function (em) {
                return Boolean($scope.checkboxes[em.data.id]);
            });
    };
    $scope.checkSelectedAll = function (group) {
        if (group !== undefined) {
            return $scope.grouped[group] &&
                _.keys($scope.grouped[group])
                .every(function (status) {
                    return $scope.checkSelectedByStatus(group, status);
                });
        } else {
            return $scope.checkup.measures &&
                $scope.checkup.measures.every(function (em) {
                    return Boolean($scope.checkboxes[em.data.id]) || !$scope.canSelectEMAppointment(em);
                });
        }
    };
    $scope.canSelectMeasureGroup = function (group, status, mcode) {
        return $scope.canSelectEMAppointment($scope.grouped[group][status][mcode][0])
    };
    $scope.canSelectEMAppointment = function (em) {
        return em.access.can_edit_appointment && (
            em.data.id || !cancelled_statuses.has(em.data.status.code)
        );
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
        EMModalService.openView(em, {'display_new_appointment': true}).then(function (action) {
            switch (action) {
                case 'execute':
                    $scope.executeEm(idx);
                    break;
                case 'cancel':
                    $scope.cancelEm(idx);
                    break;
                case 'new_appointment':
                    $scope.newAppointment(em, $scope.checkup, $scope.header);
                    break;
                case 'delete':
                    $scope.deleteEm(idx);
                    break;
                case 'restore':
                    $scope.restoreEm(idx);
                    break;
                default:
                    EventMeasureService.get(em.data.id)
                        .then(function (upd_em) {
                            $scope.checkup.measures.splice(idx, 1, upd_em);
                        });
            }
        });
    };
    $scope.executeEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        if ($scope.canExecuteEm(em)) {
            EventMeasureService.execute(em.data)
                .then(function (upd_em) {
                    $scope.checkup.measures.splice(idx, 1, upd_em);
                });
        }
    };
    $scope.cancelEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        if ($scope.canCancelEm(em)) {
            EMModalService.openCancel(em.data).then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
        }
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
            EventMeasureService.get_appointment(em, $scope.checkup.id)
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
        return EMModalService.openCreate($scope.event_id, $scope.checkup)
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
    $scope.canDeleteEm = function (em) {
        return em.access.can_delete;
    };
    $scope.canRestoreEm = function (em) {
        return em.access.can_restore;
    };
    $scope.canExecuteEm = function (em) {
        return em.access.can_execute;
    };
    $scope.canCancelEm = function (em) {
        return em.access.can_cancel;
    };
    $scope.isManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 0;
    };
    $scope.isDeletedManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 1;
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

    // init and refresh data
    var status_order = ['created', 'assigned','waiting', 'upon_med_indications', 'overdue', 'performed',
        'cancelled', 'cancelled_dupl', 'cancelled_changed_data', 'cancelled_invalid'],
        measure_types = ['lab_test', 'func_test', 'checkup', 'hospitalization'],
        recommend_types = ['healthcare', 'social_preventiv'];
    $scope.grouped = {
        listed: {},
        measures: {},
        recommendations: {},
        statuses: [],
        measures_types_info: [],
        recommend_types_info: []
    };
    var refreshGroupedData = function (measure_list) {
        var measure_types_info = {},
            recommend_types_info = {};
        $scope.grouped.measures = {};
        $scope.grouped.recommendations = {};
        $scope.grouped.measures_types_info = [];
        $scope.grouped.recommend_types_info = [];
        // measure_list is sorted by begDateTime ASC
        angular.forEach(measure_list, function (em, idx) {
            var status_code = em.data.status.code,
                type_code = em.data.measure.measure_type.code,
                m_code = em.data.measure.code;

            $scope.grouped.listed[em.data.id] = idx;

            if (measure_types.has(type_code)) {
                if (!$scope.grouped.measures[status_code]) $scope.grouped.measures[status_code] = {};
                if (!$scope.grouped.measures[status_code][m_code]) $scope.grouped.measures[status_code][m_code] = [];
                $scope.grouped.measures[status_code][m_code].push(em);
                if (!measure_types_info[m_code]) measure_types_info[m_code] = {
                    min_date: null,
                    max_date: null,
                    name: em.data.measure.name,
                    code: em.data.measure.code
                };
                measure_types_info[m_code].min_date = !measure_types_info[m_code].min_date || moment(em.data.beg_datetime)
                    .isBefore(moment(measure_types_info[m_code].min_date)) ? em.data.beg_datetime : measure_types_info[m_code].min_date;
                measure_types_info[m_code].max_date = !measure_types_info[m_code].max_date || moment(em.data.end_datetime)
                    .isAfter(moment(measure_types_info[m_code].max_date)) ? em.data.end_datetime : measure_types_info[m_code].max_date;
            }
            if (recommend_types.has(type_code)) {
                if (!$scope.grouped.recommendations[status_code]) $scope.grouped.recommendations[status_code] = {};
                if (!$scope.grouped.recommendations[status_code][m_code]) $scope.grouped.recommendations[status_code][m_code] = [];
                $scope.grouped.recommendations[status_code][m_code].push(em);
                if (!recommend_types_info[m_code]) recommend_types_info[m_code] = {
                    min_date: null,
                    max_date: null,
                    name: em.data.measure.name,
                    code: em.data.measure.code
                };
                recommend_types_info[m_code].min_date = !recommend_types_info[m_code].min_date || moment(em.data.beg_datetime)
                    .isBefore(moment(recommend_types_info[m_code].min_date)) ? em.data.beg_datetime : recommend_types_info[m_code].min_date;
                recommend_types_info[m_code].max_date = !recommend_types_info[m_code].max_date || moment(em.data.end_datetime)
                    .isAfter(moment(recommend_types_info[m_code].max_date)) ? em.data.end_datetime : recommend_types_info[m_code].max_date;
            }
        });
        angular.forEach(measure_types_info, function (info, code) {
            $scope.grouped.measures_types_info.push(info);
        });
        angular.forEach(recommend_types_info, function (info, code) {
            $scope.grouped.recommend_types_info.push(info);
        });
    };

    $scope.rbMeasureType = RefBookService.get('MeasureType');
    $scope.rbMeasureStatus = RefBookService.get('MeasureStatus');
    $scope.$on('checkupLoaded', function () {
        $q.all([$scope.rbMeasureType.loading, $scope.rbMeasureStatus.loading])
            .then(function () {
                $scope.$watchCollection('checkup.measures', function (n, o) {
                    if (!angular.equals(n, o)) {
                        refreshGroupedData(n);
                    }
                });
                refreshGroupedData($scope.checkup.measures);
                angular.forEach(status_order, function (code) {
                    $scope.grouped.statuses.push($scope.rbMeasureStatus.get_by_code(code));
                });
            });
    })
};


WebMis20.controller('EventMeasureActionViewCtrl', ['$scope', '$q', 'RisarApi', 'EMModalService',
    'EventMeasureService', 'RefBookService', EventMeasureActionViewCtrl]);