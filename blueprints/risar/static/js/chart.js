/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var reload_chart = function () {
        RisarApi.chart(undefined, ticket_id)
        .then(function (event_info) {
            $scope.chart = event_info.event;
            $scope.automagic = event_info.automagic;
        })
    };
    reload_chart();
};
