'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/em_result_edit.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Результат по мероприятию</h4>\
</div>\
<div class="modal-body">\
<section class="content">\
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
    <ui-print-button ps="ps" resolve="ps_resolve()" before-print="save_em_result(true)" fast-print="true"\
        class="pull-left"></ui-print-button>\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-primary" ng-click="save_em_result()">Сохранить</button>\
</div>');
}]);


var EMResultModalCtrl = function ($scope, $q, RisarApi, RefBookService, WMAction,
                                  PrintingService, PrintingDialog, MessageBox, event_measure, em_result) {
    $scope.ps = new PrintingService("event_measure");
    $scope.ps_resolve = function () {
        return {
            event_measure_id: event_measure.data.id
        }
    };

    function update_print_templates (context_name) {
        $scope.ps.set_context(context_name);
    }

    $scope.saveAndClose = function () {
        $scope.save_em_result().then(function () {
            $scope.$close();
        });
    };
    $scope.save_em_result = function (need_to_print) {
        var data = $scope.action.get_data(),
            event_measure_id = event_measure.data.id,
            em_result_id = em_result.id;
        return $scope.check_can_save_action()
            .then(function () {
                return RisarApi.measure.save_em_result(
                    event_measure_id,
                    em_result_id,
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
            $scope.action = $scope.action.merge(em_result);
            $scope.action.readonly = false;
            update_print_templates(em_result.action_type.context_name);
        });
    };

    $scope.init();
};


WebMis20.controller('EMResultModalCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'WMAction',
    'PrintingService', 'PrintingDialog', 'MessageBox', EMResultModalCtrl]);