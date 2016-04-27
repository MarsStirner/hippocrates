'use strict';


WebMis20.controller('ConciliumListCtrl', ['$scope', '$q', 'RisarApi', 'PrintingService', 'PrintingDialog',
    function ($scope, $q, RisarApi, PrintingService, PrintingDialog) {
        var params = aux.getQueryParams(window.location.search);
        var event_id = $scope.event_id = params.event_id;
        $scope.ps = new PrintingService("risar");
        $scope.ps.set_context("risar");
        $scope.ps_resolve = function () {
            return {
                event_id: $scope.event_id
            }
        };
        var reloadChart = function () {
            var header = RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
            });
            var chart = RisarApi.concilium.get_list(event_id).then(function (data) {
                $scope.concilium_list = data;
            });
            return $q.all([header, chart]);
        };
        $scope.open_print_window = function () {
            if ($scope.ps.is_available()){
                PrintingDialog.open($scope.ps, $scope.ps_resolve());
            }
        };
        reloadChart();
    }
]);


WebMis20.controller('ConciliumCtrl', ['$scope', '$q', 'RisarApi', 'PrintingService', 'PrintingDialog',
    function ($scope, $q, RisarApi, PrintingService, PrintingDialog) {
        var params = aux.getQueryParams(window.location.search);
        var event_id = $scope.event_id = params.event_id;
        var concilium_id = $scope.concilium_id = params.concilium_id;
        $scope.ps = new PrintingService("risar");
        $scope.ps.set_context("risar");
        $scope.ps_resolve = function () {
            return {
                event_id: $scope.event_id
            }
        };
        var reloadChart = function () {
            var header = RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
            });
            var chart = RisarApi.concilium.get(event_id, concilium_id).then(function (data) {
                $scope.concilium = data;
            });
            return $q.all([header, chart]);
        };
        $scope.open_print_window = function () {
            if ($scope.ps.is_available()){
                PrintingDialog.open($scope.ps, $scope.ps_resolve());
            }
        };
        $scope.get_members_text = function () {
            if (!$scope.concilium) return '';
            return $scope.concilium.members.map(function (member) {
                return member.doctor.name;
            }).join(', ');
        };
        reloadChart();
    }
]);