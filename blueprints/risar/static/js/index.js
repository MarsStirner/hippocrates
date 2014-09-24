/**
 * Created by mmalkov on 24.09.14.
 */
var IndexCtrl = function ($scope, RisarApi) {
    $scope.tickets = [];
    RisarApi.schedule().then(function (tickets) {
        $scope.tickets = tickets;
    })
};
WebMis20.controller('IndexCtrl', ['$scope', 'RisarApi', IndexCtrl]);
