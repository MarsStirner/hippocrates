'use strict';

var UrgentErrandsCtrl = function ($scope, $modal, RisarApi, UserErrand) {
    $scope.load_urgent_errands = function(){
        RisarApi.urgent_errands.get().then(function (result) {
            $scope.urgent_errands = result;
        });
    }

    $scope.edit_errand = function (errand, is_author) {
        errand.is_author = is_author;
        open_edit_errand(errand).result.then(
            function (rslt) {
            var result = rslt[0],
                exec = rslt[1];
            UserErrand.edit_errand(result, exec).then($scope.load_urgent_errands);
        },
            function(){
            if (!is_author && !errand.reading_date){
            UserErrand.mark_as_read(errand).then(reload_errands);
            }
        })
    };

    var open_edit_errand = function(e){
        var scope = $scope.$new();
        scope.model = e;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/create_errand.html',
            scope: scope,
            resolve: {
                model: function () {return e}
            },
            size: 'lg'
        })
    }
    $scope.load_urgent_errands();
};


WebMis20.controller('UrgentErrandsCtrl', ['$scope', '$modal', 'RisarApi', 'UserErrand',
    UrgentErrandsCtrl]);