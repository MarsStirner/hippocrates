var PatientInfoCtrl = function ($scope, $http, WMClient, PrintingService, $interval) {
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.client_id = $scope.params.client_id;
    $scope.client = new WMClient($scope.client_id);
    $scope.client.reload()
}
WebMis20.controller('PatientInfoCtrl', ['$scope', '$http', 'WMClient', 'PrintingService', PatientInfoCtrl]);