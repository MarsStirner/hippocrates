var AmbulanceIndexCtrl = function ($scope, $window, RisarApi, Config) {
    $scope.query = "";
    $scope.results = [];
    $scope.perform_search = function () {
        var data = {
            query: $scope.query || undefined,
            closed: false
        };
        if ($scope.query) {
            RisarApi.search_event_ambulance.get(data).then(function (result) {
//                $scope.pager.pages = result.total_pages;
//                $scope.pager.record_count = result.count;
                $scope.results = result.events;
            });
        }
    };
    $scope.open_patient_info = function (event_id) {
        $window.open(Config.url.ambulance_patient_info + '?event_id=' + event_id);
    };
};
