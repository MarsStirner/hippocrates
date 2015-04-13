/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventRoutingCtrl = function ($scope, $window, RisarApi) {
    var params = aux.getQueryParams($window.location.search);
    var event_id = params.event_id;
    var emergency = $scope.emergency = params.hasOwnProperty('emergency');
    var key = (emergency)?('extra_lpu'):('plan_lpu');
    var reload_chart = function () {
        return RisarApi.event_routing.get_chart(event_id)
            .then(function (data) {
                $scope.header = data.header;
                $scope.chart = data.chart;
                $scope.chart.lpu = data.chart[key];
                $scope.selected_diagnoses = data.chart.diagnoses.clone();
            });
    };
    var reload_orgs = function () {
        RisarApi.event_routing.get_destinations($scope.selected_diagnoses)
            .then(function (result) {
                $scope.orgs = result.suitable_orgs;
                var current = $scope.orgs.filter(function (org) {
                    return org.id === $scope.chart.lpu.id;
                });
                if (current.length) {
                    $scope.chart.lpu = current[0];
                }
            });
    };
    $scope.save = function () {
        RisarApi.event_routing.attach_client($scope.chart.client_id, {
            attach_type: key,
            org_id: $scope.chart.lpu.id
        }).then(function () {
            $scope.selectLpuForm.$setPristine();
        });
    };
    $scope.getCurrentLpuLabelClass = function () {
        var cur_lpu_id = safe_traverse($scope.chart, ['lpu', 'id']),
            matched = $scope.orgs.some(function (org) {
            return org.id === cur_lpu_id;
        }),
            cls = 'alert-danger';
        if (matched) {
            cls = 'alert-success';
        } else if (cur_lpu_id) {
            cls = 'alert-warning';
        }
        return cls;
    };
    $scope.getOtherRoutingText = function () {
        return emergency ? 'Плановая госпитализация' : 'Экстренная госпитализация';
    };
    $scope.getUnsavedFormText = function () {
        return 'Вы выбрали ЛПУ для госпитализации, но не сохранили его.';
    };
    $scope.selected_diagnoses = [];
    $scope.chart = {};
    $scope.orgs = [];
    reload_chart().then(function () {
        $scope.$watchCollection('selected_diagnoses', reload_orgs);
    });
};

WebMis20.controller('EventRoutingCtrl', ['$scope', '$window', 'RisarApi', EventRoutingCtrl]);