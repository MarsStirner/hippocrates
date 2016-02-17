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


WebMis20.controller('DoctorCardFillRatesCtrl', ['$scope', 'RisarApi', 'CurrentUser', DoctorCardFillRatesCtrl]);