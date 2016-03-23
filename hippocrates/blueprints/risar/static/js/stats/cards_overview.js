'use strict';

var CurrentCardsOverviewCtrl = function ($scope, RisarApi, CurrentUser) {
    var person_id = CurrentUser.id;
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.stats_data = {};

    $scope.refresh_data = function () {
        RisarApi.stats.get_current_cards_overview(person_id, $scope.curation_level_code)
            .then(function (data) {
                $scope.stats_data = data;
            });
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('CurrentCardsOverviewCtrl', ['$scope', 'RisarApi', 'CurrentUser',
    CurrentCardsOverviewCtrl]);