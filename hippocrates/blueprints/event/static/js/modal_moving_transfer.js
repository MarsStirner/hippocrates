'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/event/moving_transfer.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">' +
    '<button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>' +
        '<h4 class="modal-title">[[ isFinalMoving() ? \'Закрытие движения\' : \'Перевод в другое отделение\' ]]</h4>' +
    '</div>' +
    '<div class="modal-body">' +
        '<ng-form name="movingTransferForm">' +
            '<div ng-if="!isFinalMoving()">' +
                '<div class="row marginal">' +
                    '<div class="col-md-8">' +
                    '<label for="transfer_os" class="control-label">В какое отделение направить</label>' +
                    '<ui-select id="transfer_os" name="transfer_os" theme="select2" ' +
                            'ng-model="model.os_transfer" ng-required="true">' +
                        '<ui-select-match placeholder="Подразделение">[[$select.selected.name]]</ui-select-match>' +
                        '<ui-select-choices repeat="os in OrgStructure.objects | filter: {show: 1} | filter: $select.search">' +
                            '<div ng-bind-html="os.name | highlight: $select.search"></div>' +
                        '</ui-select-choices>' +
                    '</ui-select>' +
                    '</div>' +
                '</div>' +
                '<div class="row marginal">' +
                    '<div class="col-md-8">' +
                        '<label for="transfer_dt" class="control-label">Дата и время перевода</label>' +
                        '<wm-datetime-as id="transfer_dt" name="transfer_dt" ng-model="model.transfer_date" ' +
                            'ng-required="true">' +
                        '</wm-datetime-as>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            '<div ng-if="isFinalMoving()">' +
                '<div class="row">' +
                    '<div class="col-md-8">' +
                        '<label for="close_dt" class="control-label">Дата и время закрытия</label>' +
                        '<wm-datetime-as id="close_dt" name="close_dt" ng-model="model.close_date" ' +
                            'ng-required="true">' +
                        '</wm-datetime-as>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</ng-form>' +
    '</div>' +
    '<div class="modal-footer">' +
        '<button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>' +
        '<button type="button" class="btn btn-primary" ng-disabled="movingTransferForm.$invalid"' +
            'ng-click="saveAndClose()">Сохранить</button>' +
    '</div>');
}]);


var MovingTransferModalCtrl = function ($scope, RefBookService, WMEventService,
        current_moving, next_moving, options) {
    $scope.model = {
        os_transfer: null,
        transfer_date: null,
        close_date: null
    };
    $scope.OrgStructure = RefBookService.get('OrgStructure');

    $scope.isFinalMoving = function () {
        return options.is_final_moving;
    };
    $scope.saveMovings = function (hospForm) {
        if ($scope.isFinalMoving()) {
            current_moving.end_date = $scope.model.close_date;
            return WMEventService.save_moving(current_moving)
                .then(function (upd_moving) {
                    return [upd_moving, undefined];
                });
        } else {
            current_moving.end_date = $scope.model.transfer_date;
            current_moving.orgStructTransfer.value = $scope.model.os_transfer;
            next_moving.beg_date = moment($scope.model.transfer_date).clone().add(1, 'seconds');
            next_moving.orgStructStay.value = $scope.model.os_transfer;
            next_moving.orgStructReceived.value = current_moving.orgStructStay.value;

            return WMEventService.save_moving(current_moving)
                .then(function (upd_cur_moving) {
                    return WMEventService.save_moving(next_moving)
                        .then(function (upd_next_moving) {
                            return [upd_cur_moving, upd_next_moving];
                        });
                });
        }
    };
    $scope.saveAndClose = function (hospForm) {
        $scope.saveMovings().then(function (movings) {
            $scope.$close(movings);
        });
    };
    $scope.init = function () {
        if ($scope.isFinalMoving()) {
            $scope.model.close_date = new Date();
        } else {
            $scope.model.transfer_date = new Date();
        }
    };

    $scope.init();
};

WebMis20.controller('MovingTransferModalCtrl', ['$scope', 'RefBookService', 'WMEventService',
    MovingTransferModalCtrl]);
