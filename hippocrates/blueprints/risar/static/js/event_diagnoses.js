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
    }
    var reload_anamnesis = function () {
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;
            $scope.client_id = event.client.id;
        })
    };
    $scope.delete_diagnosis = function (diagnosis, deleted) {
        if (arguments.length == 1) {
            deleted = 1;
        }
        WMEventServices.delete_diagnosis($scope.chart.diagnoses, diagnosis, deleted);
    };
    $scope.edit_diagnosis = function (diagnosis) {
        DiagnosisModal.openDiagnosisModalRisar(diagnosis, $scope.chart);
    };
    $scope.save = function () {
        var model = $scope.chart.diagnoses;
        RisarApi.chart.save_diagnoses($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.diagnoses = data;
        })
    }
    reload_anamnesis();
};