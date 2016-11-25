'use strict';


WebMis20.controller('PredictedPregnancyCtrl', ['$scope', '$q', '$controller', 'RisarApi',
    function ($scope, $q, $controller, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $controller('commonPrintCtrl', {$scope: $scope});
    var getHeader = function () {
         RisarApi.chart.get_header(event_id).then(function (data) {
             $scope.header = data.header;
         });
    };
    getHeader();
}]);
