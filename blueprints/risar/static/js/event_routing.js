/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventRoutingCtrl = function ($scope, $window, RisarApi, TimeoutCallback, RefBookService) {
    var params = aux.getQueryParams($window.location.search);
    var event_id = params.event_id;
    var reload_chart = function () {
        RisarApi.chart.get_mini(event_id)
            .then(function (event) {
                $scope.chart = event;
                $scope.selected_diagnoses = event.diagnoses.clone()
            })
    };
    var reload_results = function () {
        RisarApi.event_routing.get($scope.selected_diagnoses)
            .then(function (results) {
                $scope.results = results;
            })
    };
    var organisations = RefBookService.get('Organisation');
    $scope.select_lpu = function (organisation) {
        $scope.chart.plan_lpu = organisations.get(organisation.id);
    };
    $scope.selected_diagnoses = [];
    $scope.chart = {};
    $scope.results = [];
    $scope.$watchCollection('selected_diagnoses', reload_results);
    reload_chart();
};
