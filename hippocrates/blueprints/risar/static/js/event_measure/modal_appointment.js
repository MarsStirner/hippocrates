'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/em_appointment_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Направление по мероприятию</h4>\
</div>\
<div class="modal-body">\
<section class="content">\
    <div class="row marginal" ng-if="appointment.number">\
        <div class="col-md-12">\
        <p class="text-right"><b>Номер направления:</b> [[appointment.number]]</p>\
        </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-body">\
                <wm-action-layout action="action"></wm-action-layout>\
            </div>\
        </div>\
    </div>\
    </div>\
</section>\
</div>\
<div class="modal-footer">\
    <ui-print-button ps="ps" resolve="ps_resolve()" before-print="save_appointment(true)" fast-print="true"\
        class="pull-left"></ui-print-button>\
    <button type="button" class="btn btn-primary" ng-click="saveAndClose()">Сохранить и закрыть</button>\
</div>');
}]);


var EMAppointmentModalCtrl = function ($scope, $q, RisarApi, RefBookService, WMAction,
                                       PrintingService, PrintingDialog, MessageBox, event_measure, appointment) {
    $scope.ro = false;
    var _saved = false;
    $scope.ps = new PrintingService("event_measure");
    $scope.ps_resolve = function () {
        return {
            event_measure_id: event_measure.data.id
        }
    };

    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    }

    $scope.close = function () {
        if (_saved) {
            $scope.$close();
        } else {
            $scope.$dismiss('cancel');
        }
    };
    $scope.saveAndClose = function () {
        $scope.save_appointment().then(function () {
            $scope.$close();
        });
    };
    $scope.save_appointment = function (need_to_print) {
        var data = $scope.action.get_data(),
            event_measure_id = event_measure.data.id,
            appointment_id = appointment.id;
        return $scope.check_can_save_action()
            .then(function () {
                return RisarApi.measure.save_appointment(
                    event_measure_id,
                    appointment_id,
                    data
                ).
                    then(function (action) {
                        _saved = true;
                        $scope.action.merge(action);
                    });
            }, function (result) {
                var deferred = $q.defer();
                if (need_to_print) {
                    if (!result.silent) {
                        MessageBox.info('Невозможно сохранить действие', result.message)
                            .then(function () {
                                deferred.resolve();
                            });
                    } else {
                        deferred.resolve();
                    }
                } else {
                    return MessageBox.error('Невозможно сохранить действие', result.message);
                }
                return deferred.promise;
            })
    };
    $scope.check_can_save_action = function () {
        var deferred = $q.defer();
        if ($scope.action.readonly) {
            deferred.reject({
                silent: true,
                message: 'Действие открыто в режиме чтения'
            });
        } else {
            deferred.resolve();
        }
        return deferred.promise;
    };

    $scope.init = function () {
        $scope.appointment = appointment;
        $scope.action = new WMAction();
        $scope.ActionStatus = RefBookService.get('ActionStatus');
        $scope.ActionStatus.loading.then(function () {
            $scope.action = $scope.action.merge(appointment);
            $scope.ro = $scope.action.readonly = $scope.action.ro = appointment.ro;
            update_print_templates(appointment.action_type.context_name);
        });
    };

    $scope.init();
};


WebMis20.controller('EMAppointmentModalCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'WMAction',
    'PrintingService', 'PrintingDialog', 'MessageBox', EMAppointmentModalCtrl]);