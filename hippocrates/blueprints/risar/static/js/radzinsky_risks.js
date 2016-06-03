'use strict';


WebMis20.controller('RadzinskyRisksCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'PrintingService', 'PrintingDialog',
    function ($scope, $q, RisarApi, RefBookService, PrintingService, PrintingDialog) {
        var params = aux.getQueryParams(window.location.search);
        var event_id = $scope.event_id = params.event_id;
        $scope.selectedStage = {id: undefined};
        $scope.header = {};
        $scope.risks = {};

        $scope.ps = new PrintingService("risar");
        $scope.ps.set_context("risar");
        $scope.ps_resolve = function () {
            return {
                event_id: $scope.event_id
            }
        };
        $scope.open_print_window = function () {
            if ($scope.ps.is_available()){
                PrintingDialog.open($scope.ps, $scope.ps_resolve());
            }
        };
        var reloadChart = function () {
            var header = RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
            });
            var chart = RisarApi.radzinsky_risks.list(event_id).then(function (data) {
                $scope.risks = data;
            });
            $scope.rbRadzStage = RefBookService.get('rbRadzStage');
            $scope.rbRadzRiskFactorGroup = RefBookService.get('rbRadzRiskFactorGroup');
            return $q.all([header, chart, $scope.rbRadzStage.loading, $scope.rbRadzRiskFactorGroup.loading]);
        };

        $scope.isStageSelected = function (stage) {
            return (stage !== undefined ? stage.id : stage) === $scope.selectedStage.id;
        };
        $scope.selectStage = function (stage) {
            return $scope.selectedStage.id = stage !== undefined ? stage.id : stage;
        };
        $scope.getRiskRateTextClass = function () {
            var r = safe_traverse($scope.risks, ['general_info', 'risk_rate']);
            if (!r) return 'empty-value';
            if (r.code === 'low') return 'text-green';
            else if (r.code === 'medium') return 'text-warning';
            else if (r.code === 'high') return 'text-danger';
            else return '';
        };

        reloadChart();
    }]);