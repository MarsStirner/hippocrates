/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, RisarApi, RisarNotificationService, Config, $timeout) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var event_id = params.event_id;
    var reload_chart = function () {
        RisarApi.chart.get(event_id, ticket_id)
        .then(function (event_info) {
            $scope.chart = event_info.event;
            if (event_info.automagic) {
                RisarNotificationService.notify(
                    200,
                    'Пациентка поставлена на учёт: <b>[[ chart.person.name ]]</b>. <a href="#">Изменить</a> <a ng-click="cancel_created()">Отменить</a>',
                    'success')
            }
            if (event_info.event.anamnesis.mother.menstruation_last_date) {
                var pregnancy_week = moment().diff(moment(event_info.event.anamnesis.mother.menstruation_last_date), 'weeks') + 1;
                if (pregnancy_week > 40) pregnancy_week = '40+';
                $scope.pregnancy_week = pregnancy_week;
            } else {
                $scope.pregnancy_week = '?'
            }

        })
    };
    $scope.cancel_created = function () {
        RisarApi.chart.delete(ticket_id).then(function success() {
            window.location.replace(Config.url.index_html);
        })
    };
    reload_chart();
};
