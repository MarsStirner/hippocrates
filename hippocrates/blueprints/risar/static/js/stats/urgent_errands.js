'use strict';

var UrgentErrandsCtrl = function ($scope, RisarApi, ErrandModalService) {
    $scope.load_urgent_errands = function(){
        RisarApi.stats.urgent_errands().then(function (result) {
            $scope.urgent_errands = result;
        });
    };

    $scope.edit_errand = function (errand) {
        var is_author = false;
        ErrandModalService.openEdit(errand, is_author)
            .then($scope.load_urgent_errands);
    };

    $scope.load_urgent_errands();
};


WebMis20.controller('UrgentErrandsCtrl', ['$scope', 'RisarApi', 'ErrandModalService',
    UrgentErrandsCtrl]);