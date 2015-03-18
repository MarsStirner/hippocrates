/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventRoutingCtrl = function ($scope, $window, RisarApi, TimeoutCallback, RefBookService) {
    var params = aux.getQueryParams($window.location.search);
    var event_id = params.event_id;
    var emergency = $scope.emergency = params.hasOwnProperty('emergency');
    var key = (emergency)?('extra_lpu'):('plan_lpu');
    var reload_chart = function () {
        RisarApi.event_routing.get_chart(event_id)
            .then(function (event) {
                $scope.chart = event;
                $scope.chart.lpu = event[key];
                $scope.selected_diagnoses = event.diagnoses.clone()
            })
    };
    var reload_results = function () {
        RisarApi.event_routing.get_destinations($scope.selected_diagnoses)
            .then(function (results) {
                $scope.results = results;
            })
    };
    var organisations = RefBookService.get('Organisation');
    $scope.select_lpu = function (organisation) {
        $scope.chart.lpu = organisations.get(organisation.id);
        $scope.save();
    };
    $scope.save = function () {
        RisarApi.event_routing.attach_client($scope.chart.client_id, {
            attach_type: key,
            org_id: $scope.chart.lpu.id
        });
    };
    $scope.selected_diagnoses = [];
    $scope.chart = {};
    $scope.results = [];
    $scope.$watchCollection('selected_diagnoses', reload_results);
    reload_chart();
};
