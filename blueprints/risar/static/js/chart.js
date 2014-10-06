/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, RisarApi, RisarNotificationService, Config, $timeout) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var event_id = params.event_id;
    var reload_chart = function () {
        RisarApi.chart(event_id, ticket_id)
        .then(function (event_info) {
            $scope.chart = event_info.event;
            if (event_info.automagic) {
                RisarNotificationService.notify(
                    200,
                    'Пациентка поставлена на учёт: <b>[[ chart.person.name ]]</b>. <a href="#">Изменить</a> <a ng-click="cancel_created()">Отменить</a>',
                    'success')
            }
        })
    };
    $scope.cancel_created = function () {
        RisarApi.chart_delete(ticket_id).then(function success() {
            window.location.replace(Config.url.index_html);
        })
    };
    reload_chart();
};
