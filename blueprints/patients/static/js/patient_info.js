var PatientInfoCtrl = function ($scope, WMClient) {
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.client_id = $scope.params.client_id;
    $scope.client = new WMClient($scope.client_id);
    $scope.client.reload();
    $scope.close_patient_info = function() {
        if (window.opener) {
            window.opener.focus();
            window.close();
        }
    }
}
WebMis20.controller('PatientInfoCtrl', ['$scope', 'WMClient', PatientInfoCtrl]);