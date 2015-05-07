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
        RisarApi.event_routing.get_destinations($scope.selected_diagnoses, $scope.chart.client.id)
            .then(function (result) {
                $scope.district_orgs = result.district_orgs;
                $scope.region_orgs = result.region_orgs;
                refreshAllOrgsList();
                setCurrentLpu();
            });
    };
    var refreshAllOrgsList = function () {
        $scope._all_orgs_list = [];
        angular.forEach($scope.district_orgs, function (org_info) {
            $scope._all_orgs_list = $scope._all_orgs_list.concat(org_info.orgs);
        });
        angular.forEach($scope.region_orgs, function (org_info) {
            $scope._all_orgs_list = $scope._all_orgs_list.concat(org_info.orgs);
        });
    };
    var setCurrentLpu = function () {
        var orgs = $scope._all_orgs_list,
            cur_lpu_id = safe_traverse($scope.chart, ['lpu', 'id']);
        for (var i = 0; i < orgs.length; i++) {
            if (orgs[i].id === cur_lpu_id) {
                $scope.chart.lpu = orgs[i];
                break;
            }
        }
    };
    $scope.save = function () {
        RisarApi.event_routing.attach_client($scope.chart.client.id, {
            attach_type: key,
            org_id: $scope.chart.lpu.id
        }).then(function () {
            $scope.selectLpuForm.$setPristine();
        });
    };
    $scope.toggleDiagnosesSelection = function () {
        if ($scope.selected_diagnoses.length === $scope.chart.diagnoses.length) {
            $scope.selected_diagnoses = [];
        } else {
            $scope.selected_diagnoses = $scope.chart.diagnoses.clone();
        }
    };
    $scope.lpuSelected = function () {
        return safe_traverse($scope.chart, ['lpu', 'id']);
    };
    $scope.currentLpuMatchesDiagnoses = function () {
        var cur_lpu_id = safe_traverse($scope.chart, ['lpu', 'id']),
            matched = $scope._all_orgs_list.some(function (org) {
                return org.id === cur_lpu_id;
            });
        return matched;
    };
    $scope.districtLpuAvailable = function () {
        return !_.isEmpty($scope.district_orgs);
    };
    $scope.regionLpuAvailable = function () {
        return !_.isEmpty($scope.region_orgs);
    };
    $scope.noLpuAvailable = function () {
        return !($scope.districtLpuAvailable() || $scope.regionLpuAvailable())
    };
    $scope.getPatientLiveAddressText = function () {
        return safe_traverse($scope.chart, ['client', 'live_address', 'text_summary'], 'Нет');
    };
    $scope.getOtherRoutingText = function () {
        return emergency ? 'Плановая госпитализация' : 'Экстренная госпитализация';
    };
    $scope.getUnsavedFormText = function () {
        return 'Вы выбрали ЛПУ для госпитализации, но не сохранили его.';
    };
    $scope.getToggleDiagnosesBtnText = function () {
        if ($scope.selected_diagnoses.length === $scope.chart.diagnoses.length) {
            return 'Очистить выбранные';
        } else {
            return 'Выбрать все'
        }
    };
    $scope.selected_diagnoses = [];
    $scope.chart = {};
    $scope.district_orgs = {};
    $scope.region_orgs = {};
    $scope._all_orgs_list = [];

    reload_chart().then(function () {
        $scope.$watchCollection('selected_diagnoses', reload_orgs);
    });
};

WebMis20.controller('EventRoutingCtrl', ['$scope', '$window', 'RisarApi', EventRoutingCtrl]);