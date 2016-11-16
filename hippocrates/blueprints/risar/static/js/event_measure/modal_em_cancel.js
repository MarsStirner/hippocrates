'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/event_measure_cancel.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Отмена мероприятия</h4>\
</div>\
<div class="modal-body">\
    <form class="form-horizontal">\
        <div class="form-group">\
            <label for="cancel_reason" class="col-sm-3 control-label">Причина отмены</label>\
            <div class="col-sm-9 form-control-static">\
                <rb-select ref-book="rbMeasureCancelReason" ng-model="model.cancel_reason" id="cancel_reason"></rb-select>\
            </div>\
        </div>\
    </form>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-warning" ng-click="cancelAndClose()">Подтвердить</button>\
</div>');
}]);


var EventMeasureCancelModalCtrl = function ($scope, EventMeasureService, event_measure) {
    $scope.model = {
        cancel_reason: undefined
    };
    $scope.cancelAndClose = function () {
        $scope.cancelEm().then($scope.$close);
    };
    $scope.cancelEm = function () {
        return EventMeasureService.cancel(event_measure, $scope.model);
    };
};


WebMis20.controller('EventMeasureCancelModalCtrl', ['$scope', 'EventMeasureService',
    EventMeasureCancelModalCtrl]);