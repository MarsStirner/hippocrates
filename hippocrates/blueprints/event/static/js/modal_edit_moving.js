'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/event/moving.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Информация о движении</h4>\
</div>\
<div class="modal-body">\
    <ng-form name="movingForm">\
    <div class="row marginal">\
        <div class="col-md-5">\
            <label for="orgStructStay" class="control-label">Поступил в отделение</label>\
            <ui-select id="orgStructStay" name="orgStructStay" theme="select2"\
                       ng-change="org_struct_changed(model)"\
                       ng-model="model.orgStructStay.value" ng-required="true">\
                <ui-select-match placeholder="Подразделение">[[$select.selected.name]]</ui-select-match>\
                <ui-select-choices repeat="os in OrgStructure.objects | filter: {show: 1} | filter: $select.search">\
                    <div ng-bind-html="os.name | highlight: $select.search"></div>\
                </ui-select-choices>\
            </ui-select>\
        </div>\
        <div class="col-md-4">\
            <label for="arrival_date" class="control-label">Дата и время поступления</label>\
            <wm-datetime-as id="arrival_date" name="arrival_date" ng-model="model.beg_date" ng-required="true">\
            </wm-datetime-as>\
        </div>\
        <div class="col-md-3">\
            <label for="patronage" class="control-label">Патронаж</label>\
            <div name="patronage">\
                <div class="radio-inline">\
                    <label>\
                        <input type="radio" name="patronage_[[$index]]"\
                               ng-model="model.patronage.value" data-ng-value="true" required>\
                        Да\
                    </label>\
                </div>\
                <div class="radio-inline">\
                    <label>\
                        <input type="radio" name="patronage_[[$index]]"\
                               ng-model="model.patronage.value" data-ng-value="false" required>\
                        Нет\
                    </label>\
                </div>\
            </div>\
        </div>\
    </div>\
    <div class="row marginal">\
        <div class="col-md-4 col-md-offset-5">\
            <label for="out_date" class="control-label">Дата выбытия</label>\
            <wm-datetime-as id="out_date" name="out_date" ng-model="model.end_date"\
                min-date="event_admission_date">\
            </wm-datetime-as>\
        </div>\
    </div>\
    <div ng-if="hospBedsSelectable()">\
        <div class="row marginal">\
            <div class="col-lg-12 col-md-12 col-sm-12">\
                <button style="margin:3px 3px;" ng-repeat="hb in model.hosp_beds" class="btn"\
                    ng-click="selectHospBed(hb)" ng-disabled="hb.occupied"\
                    ng-class="{\'btn-danger\': hb.occupied, \'btn-success\': hb.chosen}">[[hb.code]]</button>\
                <span class="text-danger" ng-if="!model.hosp_beds.length">В отделении нет коек</span>\
            </div>\
        </div>\
        <div class="row">\
            <div class="col-md-5">\
                <label for="hospitalBedProfile" class="control-label">Профиль койки</label>\
                <rb-select ng-model="model.hospitalBedProfile.value" ref-book="rbHospitalBedProfile"\
                    required></rb-select>\
            </div>\
        </div>\
    </div>\
    </ng-form>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-primary" ng-disabled="movingForm.$invalid"\
        ng-click="saveAndClose()" ng-if="btnSaveAvailable()">Сохранить</button>\
</div>');
}]);


var MovingModalCtrl = function ($scope, RefBookService, WMEventService,
        moving, options) {
    $scope.model = moving;
    $scope.create_mode = !$scope.model.id;

    $scope.OrgStructure = RefBookService.get('OrgStructure');

    $scope.hospBedsSelectable = function () {
        return options.hosp_beds_selectable;
    };


    $scope.selectHospBed = function () {
    };



//    $scope.createContract = function () {
//        var client_id = safe_traverse($scope.event, ['info', 'client', 'info', 'id']),
//            finance_id = safe_traverse($scope.event, ['info', 'event_type', 'finance', 'id']),
//            client = $scope.event.info.client;
//        AccountingService.get_contract(undefined, {
//            finance_id: finance_id,
//            client_id: client_id,
//            payer_client_id: client_id,
//            generate_number: true
//        })
//            .then(function (contract) {
//                return ContractModalService.openEdit(contract, client);
//            })
//            .then(function (result) {
//                var contract = result.contract;
//                refreshAvailableContracts()
//                    .then(function () {
//                        set_contract(contract.id)
//                    });
//            });
//    };
//    $scope.editContract = function (idx) {
//        if (!$scope.event.info.contract) return;
//        var contract = _.deepCopy($scope.event.info.contract);
//        ContractModalService.openEdit(contract)
//            .then(function (result) {
//                var upd_contract = result.contract;
//                refreshAvailableContracts()
//                    .then(function () {
//                        set_contract(upd_contract.id)
//                    });
//            });
//    };
//    $scope.saveEvent = function (hospForm) {
//        var deferred = $q.defer();
//        $scope.editing.submit_attempt = true;
//        if (hospForm.$valid) {
//            WMEventService.save_hosp($scope.event).then(function (result) {
//                hospForm.$setPristine();
//                $scope.refreshEvent(result.id)
//                    .then(function () {
//                        deferred.resolve($scope.event);
//                    });
//            });
//        } else {
//            deferred.reject();
//        }
//        return deferred.promise;
//    };
    $scope.saveAndClose = function (hospForm) {
        $scope.saveEvent(hospForm).then(function (event) {
            $scope.$close($scope.event);
        });
    };
};


WebMis20.controller('MovingModalCtrl', ['$scope', 'RefBookService', 'WMEventService',
    MovingModalCtrl]);
