/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var InspectionPuerperaViewCtrl = function ($scope, $modal, RisarApi, PrintingService, PrintingDialog) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_fi = new PrintingService("risar_inspection");
    $scope.ps_fi.set_context("risar_osm1_talon");

    $scope.checkups = [];
    $scope.checkupsAccess = [];

    $scope.ps_resolve = function (checkup_id) {
        return {
            event_id: $scope.header.event.id,
            action_id: checkup_id
        }
    };
    $scope.print_checkup_ticket = function (checkup, fmt) {
        // Вы потом не разберётесь, откуда у этого говна ноги растут. Простите. Я не хотел
        var ticket_id = checkup.ticket_25.id;
        RisarApi.print_ticket_25(ticket_id, fmt);
    };
    $scope.open_print_window = function (ps, checkup_id) {
        if (ps.is_available()){
            PrintingDialog.open(ps, $scope.ps_resolve(checkup_id));
        }
    };
    $scope.canEditCheckup = function (idx) {
        return $scope.checkupsAccess.length && $scope.checkupsAccess[idx].can_edit;
    };

    var reload = function () {
        $scope.checkups = [];
        $scope.checkupsAccess = [];
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
            });
        RisarApi.checkup_puerpera.get_list(event_id)
            .then(function (data) {
                angular.forEach(data.checkups, function (d) {
                    $scope.checkups.push(d.checkup);
                    $scope.checkupsAccess.push(d.access);
                });

            });
    };

    $scope.init();
    reload();
};

WebMis20.controller('InspectionPuerperaViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog',
    InspectionPuerperaViewCtrl]);
