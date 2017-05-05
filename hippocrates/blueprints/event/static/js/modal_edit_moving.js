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
                       ng-change="onOrgStructStayChanged()"\
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
            <wm-datetime-as id="out_date" name="out_date" ng-model="model.end_date">\
            </wm-datetime-as>\
        </div>\
    </div>\
    <div ng-if="hospBedsSelectable()">\
        <div class="row marginal">\
            <div class="col-lg-12 col-md-12 col-sm-12">\
                <button style="margin:3px 3px;" ng-repeat="hb in hospBedList" class="btn"\
                    ng-click="selectHospBed(hb)" ng-disabled="hb.occupied"\
                    ng-class="{\'btn-danger\': hb.occupied, \'btn-success\': hb.chosen}">[[hb.code]]</button>\
                <span class="text-danger" ng-if="!hospBedList.length">В отделении нет коек</span>\
            </div>\
        </div>\
        <div class="row" ng-if="hospBedList.length">\
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
        ng-click="saveAndClose()">Сохранить</button>\
</div>');
}]);


var MovingModalCtrl = function ($scope, RefBookService, WMEventService,
        moving, options) {
    $scope.model = moving;
    $scope.create_mode = !$scope.model.id;
    $scope.hospBedList = [];

    $scope.OrgStructure = RefBookService.get('OrgStructure');

    $scope.hospBedsSelectable = function () {
        return options.hosp_beds_selectable;
    };
    $scope.selectHospBed = function (hb) {
        $scope.hospBedList.map(function (hbed) {
            hbed.chosen = false;
        });
        $scope.model.hospitalBed.value = hb;
        $scope.model.hospitalBedProfile.value = hb.profile;
        hb.chosen = true;
    };
    $scope.onOrgStructStayChanged = function () {
        $scope.model.hospitalBedProfile.value = null;
        $scope.refreshHospBeds();
    };
    $scope.refreshHospBeds = function () {
        return WMEventService.get_available_hosp_beds(
            safe_traverse($scope.model, ['orgStructStay', 'value', 'id']),
            safe_traverse($scope.model, ['hospitalBedProfile', 'value', 'id'])
        )
            .then(function (result) {
                $scope.hospBedList = result;
            });
    };

//    $scope.close_last_moving = function(){
//        var moving = $scope.event.movings.length ? $scope.event.movings[$scope.event.movings.length - 1] : null;
//        return ApiCalls.wrapper('POST', WMConfig.url.event.moving_close, {}, moving).then(function(result){
//            $scope.refreshMovings();
//        })
//    };


    $scope.saveMoving = function () {
        return WMEventService.save_moving($scope.model);
    };
    $scope.saveAndClose = function () {
        $scope.saveMoving()
            .then(function (moving) {
                $scope.$close(moving);
            });
    };

    $scope.refreshHospBeds();
};


WebMis20.controller('MovingModalCtrl', ['$scope', 'RefBookService', 'WMEventService',
    MovingModalCtrl]);
