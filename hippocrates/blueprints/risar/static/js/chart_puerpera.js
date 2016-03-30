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
    $scope.ps_resolve = function (checkup_id) {
        return {
            event_id: $scope.header.event.id,
            action_id: checkup_id
        }
    };

    var reload = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.checkup_puerpera.get_list(event_id)
            .then(function (data) {
                $scope.checkups = data.checkups;
            });
    };

    $scope.open_print_window = function (ps, checkup_id) {
        if (ps.is_available()){
            PrintingDialog.open(ps, $scope.ps_resolve(checkup_id));
        }
    };
    reload();
};

WebMis20.controller('InspectionPuerperaViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog',
    InspectionPuerperaViewCtrl]);
