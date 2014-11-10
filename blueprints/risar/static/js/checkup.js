
'use strict';
var CheckupCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;
    var reload_checkup = function () {
        RisarApi.chart.get(event_id)
        .then(function (data) {
            $scope.chart = data.event;
            $scope.client_id = data.event.client.id;
            $scope.checkup = data.event.checkups.filter(function(elem){return elem.id == checkup_id})[0]
        })
    };
    reload_checkup();
}

var CheckupFirstEditCtrl = function ($scope, RisarApi) {
    $scope.save = function () {
        var model = $scope.checkup;
        RisarApi.checkup.save($scope.checkup.id, model)
        .then(function (data) {
            $scope.checkup = data;
        })
    }
};