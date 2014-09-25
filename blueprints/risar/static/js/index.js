/**
 * Created by mmalkov on 24.09.14.
 */
var IndexCtrl = function ($scope, RisarApi) {
    $scope.date = new Date();
    $scope.tickets = [];
    RisarApi.schedule($scope.date).then(function (tickets) {
        $scope.tickets = tickets;
    })
};
