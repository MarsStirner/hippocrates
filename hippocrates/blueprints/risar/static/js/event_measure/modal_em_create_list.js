'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/em_create_list.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Добавление мероприятия</h4>\
</div>\
<div class="modal-body">\
<section class="content">\
    <ng-form name="choseMeasureForm" class="form-horizontal">\
        <div class="form-group">\
            <label for="measure_type" class="col-md-2 control-label">Название</label>\
            <div class="col-md-7">\
                <rb-select ref-book="Measure" ng-model="new_em.measure" id="measure_type"></rb-select>\
            </div>\
            <div class="cold-md-3">\
                <button type="button" class="btn btn-primary" ng-click="addNewEm()">Добавить</button>\
            </div>\
        </div>\
    </ng-form>\
    <hr>\
    <div class="row">\
    <div class="col-md-12">\
        <h4>Будут добавлены</h4>\
        <table class="table table-striped">\
            <thead>\
                <tr>\
                    <th width="50%">Название</th>\
                    <th>Дата начала</th>\
                    <th>Дата окончания</th>\
                    <th></th>\
                </tr>\
            </thead>\
            <tbody>\
                <tr ng-repeat="em in new_em.list">\
                    <td ng-bind="em.data.measure.name"></td>\
                    <td><wm-date ng-model="em.data.beg_datetime"></wm-date></td>\
                    <td><wm-date ng-model="em.data.end_datetime"></wm-date></td>\
                    <td>\
                        <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-click="removeNewEm($index)">\
                            <i class="fa fa-trash"></i></button>\
                    </td>\
                <tr>\
            </tbody>\
        </table>\
    </div>\
    </div>\
</section>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-primary" ng-click="saveAndClose()" ng-disabled="!canSave()">Сохранить</button>\
</div>');
}]);


var EMCreateListModalCtrl = function ($scope, EventMeasureService, event_id) {
    $scope.new_em = {
        measure: undefined,
        list: []
    };

    $scope.addNewEm = function () {
        EventMeasureService.get(undefined, {
            event_id: event_id,
            measure_id: $scope.new_em.measure.id
        }).then(function (em) {
            $scope.new_em.list.push(em);
        });
    };
    $scope.removeNewEm = function (idx) {
        $scope.new_em.list.splice(idx, 1);
    };

    $scope.saveAndClose = function () {
        $scope.save_em_list().then(function () {
            $scope.$close();
        });
    };
    $scope.save_em_list = function () {
        return EventMeasureService.save_em_list(event_id, $scope.new_em.list);
    };

    $scope.canSave = function () {
        return $scope.new_em.list.length;
    };

    //$scope.init = function () {};
    //
    //$scope.init();
};


WebMis20.controller('EMResultModalCtrl', ['$scope', 'EventMeasureService', EMResultModalCtrl]);