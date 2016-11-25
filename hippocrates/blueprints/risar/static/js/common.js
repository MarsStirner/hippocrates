'use strict';

//выносим все одинаковое сюда
WebMis20.controller('commonPrintCtrl', ['$scope', 'PrintingService', 'PrintingDialog',
    function($scope, PrintingService, PrintingDialog) {
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
}]);

WebMis20.controller('commonHeaderCtrl', ['$scope', 'RisarApi', function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    var getHeader = function () {
         var header = RisarApi.chart.get_header(event_id).then(function (data) {
             $scope.header = data.header;
         });
    };
    getHeader();
}]);
