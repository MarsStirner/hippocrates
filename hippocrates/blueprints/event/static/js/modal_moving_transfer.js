'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/event/moving_transfer.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">[[ isFinalMoving() ? 'Закрытие движения' : 'Перевод в другое отделение'</h4>\
</div>\
<div class="modal-body">\
    <ng-form name="movingTransferForm">\
    <div ng-if="!isFinalMoving()">
        <div class="row marginal">
            <div class="col-md-6">
                <label for="transfer_os" class="control-label">В какое отделение направить</label>
                <ui-select id="transfer_os" name="transfer_os" theme="select2"
                           ng-model="model.orgStructStay.value" ng-required="true">
                    <ui-select-match placeholder="Подразделение">[[$select.selected.name]]</ui-select-match>
                    <ui-select-choices repeat="os in OrgStructure.objects | filter: {show: 1} | filter: $select.search">
                        <div ng-bind-html="os.name | highlight: $select.search"></div>
                    </ui-select-choices>
                </ui-select>
            </div>
        </div>
        <div class="row">
            <div class="col-md-8">
                <label for="transfer_dt" class="control-label">Дата и время перевода</label>
                <wm-datetime-as id="transfer_dt" name="transfer_dt" ng-model="model.beg_date" ng-required="true">
                </wm-datetime-as>
            </div>
        </div>
    </div>
    <div ng-if="isFinalMoving()">\
        <div class="row">
            <div class="col-md-8">
                <label for="close_dt" class="control-label">Дата и время закрытия</label>
                <wm-datetime-as id="close_dt" name="close_dt" ng-model="model.beg_date" ng-required="true">
                </wm-datetime-as>
            </div>
        </div>
    </div>\
    </ng-form>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-primary" ng-disabled="movingTransferForm.$invalid"\
        ng-click="saveAndClose()" ng-if="btnSaveAvailable()">Сохранить</button>\
</div>');
}]);


var MovingTransferModalCtrl = function ($scope, CurrentUser, RefBookService, WMEventService,
        moving, options) {
    $scope.model = moving;
    $scope.create_mode = !$scope.event.event_id;

    $scope.OrgStructure = RefBookService.get('OrgStructure');

    $scope.hospBedsSelectable = function () {
        return options.hosp_beds_selectable;
    };


    $scope.selectHospBed = function () {
    };



    $scope.createContract = function () {
        var client_id = safe_traverse($scope.event, ['info', 'client', 'info', 'id']),
            finance_id = safe_traverse($scope.event, ['info', 'event_type', 'finance', 'id']),
            client = $scope.event.info.client;
        AccountingService.get_contract(undefined, {
            finance_id: finance_id,
            client_id: client_id,
            payer_client_id: client_id,
            generate_number: true
        })
            .then(function (contract) {
                return ContractModalService.openEdit(contract, client);
            })
            .then(function (result) {
                var contract = result.contract;
                refreshAvailableContracts()
                    .then(function () {
                        set_contract(contract.id)
                    });
            });
    };
    $scope.editContract = function (idx) {
        if (!$scope.event.info.contract) return;
        var contract = _.deepCopy($scope.event.info.contract);
        ContractModalService.openEdit(contract)
            .then(function (result) {
                var upd_contract = result.contract;
                refreshAvailableContracts()
                    .then(function () {
                        set_contract(upd_contract.id)
                    });
            });
    };
    $scope.saveEvent = function (hospForm) {
        var deferred = $q.defer();
        $scope.editing.submit_attempt = true;
        if (hospForm.$valid) {
            WMEventService.save_hosp($scope.event).then(function (result) {
                hospForm.$setPristine();
                $scope.refreshEvent(result.id)
                    .then(function () {
                        deferred.resolve($scope.event);
                    });
            });
        } else {
            deferred.reject();
        }
        return deferred.promise;
    };
    $scope.saveAndClose = function (hospForm) {
        $scope.saveEvent(hospForm).then(function (event) {
            $scope.$close($scope.event);
        });
    };
};


WebMis20.controller('MovingTransferModalCtrl', ['$scope', '$q', 'PrintingService',
    'WMConfig', 'CurrentUser', 'RefBookService', 'EventType', 'AccountingService',
    'ContractModalService', 'WMWindowSync', 'WMEventFormState', 'WMEventService',
    MovingTransferModalCtrl]);
