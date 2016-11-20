'use strict';

var EventDiagnosesCtrl = function ($scope, RisarApi, DiagnosisModal, WMEventServices, PrintingService, PrintingDialog) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_resolve = function () {
        return {
            event_id: event_id
        }
    };
    $scope.open_print_window = function () {
        if ($scope.ps.is_available()){
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
    };
    var reload_anamnesis = function () {
        RisarApi.chart.get_header(event_id).then(function (data) {
            $scope.header = data.header;
        });
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;
            $scope.client_id = event.client.id;
        })
    };
    reload_anamnesis();
};