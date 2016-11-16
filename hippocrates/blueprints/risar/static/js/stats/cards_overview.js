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
    $scope.getExtendedSearchUrl = function (type) {
        var args = {
            request_type: 'pregnancy',
            person_id: CurrentUser.get_main_user().id,
            closed: false
        };
        if (type === 'all') {

        } else if (type === 'not_closed45') {
            args.preg_week_min = 45;
        } else if (type === 'missed_inspection') {
            args.latest_inspection_gt = 60;
        } else if (type === 'undefined_prenatal_risks') {
            args.risk_rate = 'undefined';
        }
        return RisarApi.search_event.getExtendedSearchUrl(args);
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('CurrentCardsOverviewCtrl', ['$scope', 'RisarApi', 'CurrentUser',
    CurrentCardsOverviewCtrl]);