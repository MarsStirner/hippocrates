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