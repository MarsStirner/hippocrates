'use strict';

var DoctorCardFillRatesCtrl = function ($scope, RisarApi, CurrentUser) {
    var doctor_id = CurrentUser.id;
    $scope.stats_data = {};
    $scope.refresh_data = function () {
        RisarApi.stats.get_doctor_card_fill_rates(doctor_id)
            .then(function (data) {
                $scope.stats_data = data;
            });
    };
    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


var CardFillRatesLpuOverviewCtrl = function ($scope, RisarApi, CurrentUser) {
    var curator_id = CurrentUser.id;
    $scope.stats_data = [];
    $scope.refresh_data = function () {
        RisarApi.stats.get_card_fill_rates_overview_lpu(curator_id)
            .then(function (data) {
                $scope.stats_data = data;
            });
    };
    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


var CardFillRatesDoctorOverviewCtrl = function ($scope, RisarApi, CurrentUser) {
    var curator_id = CurrentUser.id;
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.stats_data = [];
    $scope.widget_data = [{
        key: 'Series 1',
        values: $scope.stats_data,
        color: '#dd4b39'
    }];

    var makeStatsItem = function (stat) {
        return [stat.doctor_name, stat.cfr_not_filled];
    };
    $scope.refresh_data = function () {
        RisarApi.stats.get_card_fill_rates_overview_doctor(curator_id, $scope.curation_level_code)
            .then(function (data) {
                // update stats data array with first 5 new items
                var new_data = data.slice(0, 5).map(makeStatsItem);
                $scope.stats_data = new_data;
                $scope.widget_data = [{
                    key: 'Series 1',
                    values: $scope.stats_data,
                    color: '#dd4b39'
                }];
            });
    };
    var format = d3.format('.0f');
    $scope.chartValueFormatFunction = function() {
        return function (d) {
            return format(d);
        }
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('DoctorCardFillRatesCtrl', ['$scope', 'RisarApi', 'CurrentUser', DoctorCardFillRatesCtrl]);
WebMis20.controller('CardFillRatesLpuOverviewCtrl', ['$scope', 'RisarApi', 'CurrentUser',
    CardFillRatesLpuOverviewCtrl]);
WebMis20.controller('CardFillRatesDoctorOverviewCtrl', ['$scope', 'RisarApi', 'CurrentUser',
    CardFillRatesDoctorOverviewCtrl]);