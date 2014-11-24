/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, $modal, RisarApi, RisarNotificationService, Config, $timeout) {
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
            var mld = safe_traverse(event_info, 'event.anamnesis.mother.menstruation_last_date');
            if (mld) {
                var pregnancy_week = moment().diff(moment(mld), 'weeks') + 1;
                if (pregnancy_week > 40) pregnancy_week = '40+';
                $scope.pregnancy_week = pregnancy_week;
            } else {
                $scope.pregnancy_week = ''
            }
        })
    };
    var open_attach_lpu_edit = function () {
        var scope = $scope.$new();
        scope.model = $scope.chart.client.attach_lpu;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/attach_lpu.html',
            scope: scope,
            size: 'lg'
        })
    };
    $scope.cancel_created = function () {
        RisarApi.chart.delete(ticket_id).then(function success() {
            window.location.replace(Config.url.index_html);
        })
    };
    $scope.attach_lpu_edit = function () {
        open_attach_lpu_edit().result.then(function (result) {
            RisarApi.attach_lpu.save($scope.chart.client.id, result);
        }, function(){
            reload_chart();
        });
    };

    reload_chart();
};
