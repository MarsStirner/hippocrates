var PatientEventsCtrl = function ($scope, $http, WMConfig) {
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.client_id = $scope.params.client_id;
    $scope.initialize = function() {
        $http.get(
            WMConfig.url.patients.client_events, {
                params: {
                    client_id: $scope.client_id
                }
            }
        ).success(function (data) {
            $scope.client = data.result;
        })
    };
    $scope.openEvent = function(event_id) {
         window.open(WMConfig.url.event.html.event_info + '?event_id=' + event_id, '_blank');
    };
    $scope.initialize();
};
WebMis20.controller('PatientEventsCtrl', ['$scope', '$http', 'WMConfig', PatientEventsCtrl]);
