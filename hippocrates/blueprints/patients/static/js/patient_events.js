var PatientEventsCtrl = function ($scope, $http) {
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.client_id = $scope.params.client_id;
    $scope.initialize = function() {
        $http.get(
            url_client_patients, {
                params: {
                    client_id: $scope.client_id
                }
            }
        ).success(function (data) {
            $scope.client = data.result;
        })
    }
    $scope.open_event = function(event_id) {
         window.open(url_for_event_html_event_info + '?event_id=' + event_id, '_blank');
    };
    $scope.initialize();
}
WebMis20.controller('PatientEventsCtrl', ['$scope', '$http', PatientEventsCtrl]);
