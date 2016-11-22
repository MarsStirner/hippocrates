'use strict';

var ControlledEventsStatsCtrl = function ($scope, RisarApi, CurrentUser) {
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.stats_data = {};

    $scope.refresh_data = function () {
        RisarApi.stats.controlled_events($scope.curation_level_code)
            .then(function (data) {
                $scope.stats_data = data;
            });
    };
    $scope.getExtendedSearchUrl = function () {
        var args = {
            closed: false,
            controlled_events: true
        };
        if (!$scope.curation_level_code) {
            args.person_id = CurrentUser.get_main_user().id;
        }
        return RisarApi.search_event.getExtendedSearchUrl(args);
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('ControlledEventsStatsCtrl', ['$scope', 'RisarApi', 'CurrentUser', ControlledEventsStatsCtrl]);