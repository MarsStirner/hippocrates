'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/en_appointment_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Направление по мероприятию</h4>\
</div>\
<div class="modal-body">\
<section class="content">\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
        <div class="box-body">\
            <div class="form-horizontal">\
            <div class="row">\
                <div class="col-md-12">\
                    <div class="form-group">\
                        <label for="direction_date" class="col-md-1 control-label">Назначено</label>\
                        <div class="col-md-4">\
                            <div class="row">\
                            <div class="col-md-7">\
                                <wm-date id="direction_date" name="direction_date" ng-model="action.direction_date"></wm-date>\
                            </div>\
                            <div class="col-md-5">\
                                <wm-time id="direction_date" name="direction_date" ng-model="action.direction_date"></wm-time>\
                            </div>\
                            </div>\
                        </div>\
                        <div class="col-md-1">\
                            <div class="checkbox">\
                                <label><input type="checkbox" ng-model="action.is_urgent"></label>Срочно\
                            </div>\
                        </div>\
                    </div>\
                </div>\
            </div>\
            <div class="row" ng-if="!is_med_doc()">\
                <div class="col-md-12">\
                    <div class="form-group">\
                        <label for="set_person" class="col-md-1 control-label">Назначил</label>\
                        <div class="col-md-6">\
                            <wm-person-select id="set_person" name="set_person" ng-model="action.set_person" theme="bootstrap"\
                                placeholder="Введите ФИО врача или специальность"></wm-person-select>\
                        </div>\
                    </div>\
                </div>\
            </div>\
            <div class="row">\
                <div class="col-md-12">\
                    <div class="form-group">\
                        <label for="status" class="col-md-1 control-label">Состояние</label>\
                        <div class="col-md-1">\
                            <select class="form-control" id="status" name="status"\
                                    ng-model="action.status" ng-change="on_status_changed()"\
                                    ng-options="status as status.name for status in ActionStatus.objects track by status.id">\
                            </select>\
                        </div>\
                        <label for="beg_date" class="col-md-1 control-label">Начато</label>\
                        <div class="col-md-4">\
                            <div class="row">\
                            <div class="col-md-7">\
                                <wm-date id="beg_date" name="beg_date" ng-model="action.beg_date"></wm-date>\
                            </div>\
                            <div class="col-md-5">\
                                <wm-time id="beg_date" name="beg_date" ng-model="action.beg_date"></wm-time>\
                            </div>\
                            </div>\
                        </div>\
                        <label for="end_date" class="col-md-1 control-label">Выполнено</label>\
                        <div class="col-md-4">\
                            <div class="row">\
                            <div class="col-md-7">\
                                <wm-date id="end_date" name="end_date" ng-model="action.end_date"></wm-date>\
                            </div>\
                            <div class="col-md-5">\
                                <wm-time id="end_date" name="end_date" ng-model="action.end_date"></wm-time>\
                            </div>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
            </div>\
            <div class="row">\
                <div class="col-md-12">\
                    <div class="form-group">\
                        <label for="note" class="col-md-1 control-label">Примечания</label>\
                        <div class="col-md-6">\
                            <input type="text" id="note" name="note" class="form-control" ng-model="action.note">\
                        </div>\
                    </div>\
                </div>\
            </div>\
            </div>\
        </div>\
        </div>\
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
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отменить</button>\
    <button type="button" class="btn btn-primary" ng-click="saveAndClose()">Сохранить</button>\
</div>');
}]);


var EMAppointmentModalCtrl = function ($scope, $window, $q, RisarApi, RefBookService, WMAction,
                                       PrintingService, PrintingDialog, MessageBox, event_measure, appointment) {
    $scope.ps = new PrintingService("event_measure");
    $scope.ps_resolve = function () {
        return {
            event_measure_id: event_measure.data.id
        }
    };

    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    }
    function process_printing() {
        if ($window.sessionStorage.getItem('open_action_print_dlg')) {
            $window.sessionStorage.removeItem('open_action_print_dlg');
            PrintingDialog.open($scope.ps, $scope.ps_resolve(), undefined, true);
        }
    }

    $scope.on_status_changed = function () {
        if ($scope.action.status.code === 'finished') {
            if (!$scope.action.end_date) {
                $scope.action.end_date = new Date();
            }
        } else {
            $scope.action.end_date = null;
        }
    };
    $scope.$watch('action.end_date', function (newVal, oldVal) {
        if (newVal) {
            if ($scope.action.status.code !== 'finished') {
                $scope.action.status = $scope.ActionStatus.get_by_code('finished');
            }
        } else {
            $scope.action.status = $scope.ActionStatus.get_by_code('started');
        }
    });

    $scope.saveAndClose = function () {
        $scope.save_appointment().then(function () {
            $scope.$close();
        });
    };
    $scope.save_appointment = function (need_to_print) {
        var was_new = $scope.action.is_new(),
            data = $scope.action.get_data(),
            event_measure_id = event_measure.data.id,
            appointment_id = appointment.id;
        return $scope.check_can_save_action()
            .then(function () {
                if (was_new && need_to_print) { $window.sessionStorage.setItem('open_action_print_dlg', true) }
                return RisarApi.measure.save_appointment(
                    event_measure_id,
                    appointment_id,
                    data
                ).
                    then(function (action) {
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
            });
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
        $scope.action = new WMAction();
        $scope.ActionStatus = RefBookService.get('ActionStatus');
        $scope.ActionStatus.loading.then(function () {
            $scope.action = $scope.action.merge(appointment);
            $scope.action.readonly = false;
            update_print_templates(appointment.action_type.context_name);
            process_printing();
        });
    };

    $scope.init();
};


WebMis20.controller('EMAppointmentModalCtrl', ['$scope', '$window', '$q', 'RisarApi', 'RefBookService', 'WMAction',
    'PrintingService', 'PrintingDialog', 'MessageBox', EMAppointmentModalCtrl]);