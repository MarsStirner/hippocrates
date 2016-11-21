'use strict';

var ControlledEventsStatsCtrl = function ($scope, RisarApi, CurrentUser) {
    $scope.stats_data = {};

    $scope.refresh_data = function () {
        RisarApi.stats.controlled_events()
            .then(function (data) {
                $scope.stats_data = data;
            });
    };
    $scope.getExtendedSearchUrl = function () {
        var args = {
            request_type: 'pregnancy',
            person_id: CurrentUser.get_main_user().id,
            closed: false,
            controlled_events: true
        };
        return RisarApi.search_event.getExtendedSearchUrl(args);
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('ControlledEventsStatsCtrl', ['$scope', 'RisarApi', 'CurrentUser', ControlledEventsStatsCtrl]);