
'use strict';
var EpicrisisCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    var reload_epicrisis = function () {
        RisarApi.chart.get(event_id)
        .then(function (data) {
            $scope.chart = data.event;
        })
    };
    $scope.save = function () {
        var model = $scope.chart.epicrisis;
        RisarApi.epicrisis.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.epicrisis = data;
        })
    }
    reload_epicrisis();
}