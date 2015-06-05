'use strict';

var EventDiagnosesCtrl = function ($scope, RisarApi, DiagnosisModal, WMEventServices) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
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