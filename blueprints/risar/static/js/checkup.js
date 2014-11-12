
'use strict';
var CheckupCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id
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

var CheckupFirstEditCtrl = function ($scope, $window, RisarApi, Config) {
    $scope.save = function () {
        if($scope.checkup){
            $scope.checkup.flat_code = 'risarFirstInspection';
        } else {
            $scope.checkup = {flat_code: 'risarFirstInspection'};
        }
        var model = $scope.checkup;
        RisarApi.checkup.save($scope.event_id, model)
        .then(function (data) {
            if($scope.checkup.id){
                $scope.checkup = data;
            } else {
                $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id + '&checkup_id=' + data.id, '_self');
            }

        })
    }
};