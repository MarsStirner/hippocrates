'use strict';

WebMis20.run(['$templateCache', '$http', function ($templateCache, $http) {
    $http.get('/risar/static/templates/event_measure_view.html').then(function(response) {
        $templateCache.put('/WebMis20/RISAR/modal/event_measure_view.html', response.data);
    });
}]);

var EventMeasureModalCtrl = function ($scope, $filter, $q,
    RisarApi, RefBookService, WMAction, PrintingService, EMModalService,
    event_measure, options) {
    $scope.event_measure = event_measure.data;
    $scope.access = event_measure.access
    $scope.ro = true;
    $scope.ps = new PrintingService("event_measure");
    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    };
    $scope.setTab = function (num) {
        $scope.tabNum = num;
    };

    $scope.canEditEmAppointment = function () {
        return $scope.access.can_edit_appointment;
    };
    $scope.canEditEmResults = function () {
        return $scope.access.can_edit_result;
    };
    $scope.canReadEmAppointment = function () {
        return $scope.access.can_read_appointment;
    };
    $scope.canReadEmResult = function () {
        return $scope.access.can_read_result;
    };
    $scope.canExecuteEm = function () {
        return $scope.access.can_execute;
    };
    $scope.canCancelEm = function (em) {
        return $scope.access.can_cancel;
    };
    $scope.canNewAppointment = function () {
        return options && options.display_new_appointment && $scope.event_measure.measure.measure_type.code === 'checkup';
    };
    $scope.canDelete = function () {
        return $scope.access.can_delete;
    };
    $scope.canRestore = function () {
        return $scope.access.can_restore;
    };
    $scope.displayNewAppointment = function () {
        return options && options.display_new_appointment;
    };

    $scope.editAppointment = function () {
        var appointment = _.deepCopy($scope.appointment);
        EMModalService.openAppointmentEdit(event_measure, appointment).then($scope.refresh);
    };
    $scope.editEmResults = function () {
        var em_result = _.deepCopy($scope.em_result);
        EMModalService.openEmResultEdit(event_measure, em_result).then($scope.refresh);
    };
    $scope.getSchemeInfo = function () {
        if($scope.event_measure.scheme) {
            return '{0}{. |1}'.formatNonEmpty($scope.event_measure.scheme.number, $scope.event_measure.scheme.name);
        }
    };
    $scope.getMeasureDateRange = function () {
        return '{0}{ - |1}'.formatNonEmpty(
            $filter('asDateTime')($scope.event_measure.beg_datetime),
            $filter('asDateTime')($scope.event_measure.end_datetime)
        );
    };
    $scope.getRealizationDate = function () {
        return $scope.event_measure.realization_date || '';
    };
    $scope.getMeasureCreateInfo = function () {
        return '{0}{, |1}'.formatNonEmpty(
            $filter('asDateTime')($scope.event_measure.create_datetime),
            safe_traverse($scope.event_measure, ['create_person', 'short_name'])
        );
    };
    $scope.getMeasureModifyInfo = function () {
        return '{0}{, |1}'.formatNonEmpty(
            $filter('asDateTime')($scope.event_measure.modify_datetime),
            safe_traverse($scope.event_measure, ['modify_person', 'short_name'])
        );
    };
    $scope.getAppointmentInfo = function () {
        return $scope.event_measure.appointment_action_id || '';
    };
    $scope.getAppointmentComment = function () {
        return $scope.event_measure.appointment_comment || '';
    };

    $scope.refresh = function () {
        return RisarApi.measure.get_info($scope.event_measure.id, $scope.event_measure.appointment_action_id).then(function(data){
            $scope.event_measure = data.event_measure;
            $scope.appointment = data.appointment;
            $scope.em_result = data.em_result;
            if ($scope.appointment) {
                $scope.appointment_action = $scope.appointment_action.merge($scope.appointment);
                $scope.appointment_action.readonly = $scope.appointment_action.ro = $scope.ro;
                update_print_templates($scope.appointment.action_type.context_name);
            }
            if ($scope.em_result) {
                $scope.em_result_action = $scope.em_result_action.merge($scope.em_result);
                $scope.em_result_action.readonly = $scope.em_result_action.ro = $scope.ro;
                update_print_templates($scope.em_result.action_type.context_name);
            }
        })
    };

    $scope.init = function () {
        $scope.appointment_action = new WMAction();
        $scope.em_result_action = new WMAction();
        $scope.ActionStatus = RefBookService.get('ActionStatus');
        $scope.FileAttachType = RefBookService.get('FileAttachType');
        $q.all([$scope.ActionStatus.loading, $scope.FileAttachType.loading]).then(function () {
            $scope.action_attach_type_id = $scope.FileAttachType.get_by_code('action').id;
            $scope.refresh();
        });
    };
    $scope.init();
};


WebMis20.controller('EventMeasureModalCtrl', [
    '$scope', '$filter', '$q',
    'RisarApi', 'RefBookService', 'WMAction', 'PrintingService', 'EMModalService',
    EventMeasureModalCtrl]);