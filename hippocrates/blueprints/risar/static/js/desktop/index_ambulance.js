var AmbulanceIndexCtrl = function ($scope, $window, RisarApi, Config) {
    $scope.results = [];
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
    };

    $scope.perform_search = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var data = {
            page: $scope.pager.current_page,
            query: $scope.query || undefined,
            closed: false
        };
        if ($scope.query) {
            RisarApi.search_event_ambulance.get(data).then(function (result) {
                $scope.pager.pages = result.total_pages;
                $scope.pager.record_count = result.count;
                $scope.results = result.events;
            });
        }
    };

    try {
        $scope.query = JSON.parse($window.sessionStorage.getItem('query'));
        $window.sessionStorage.removeItem('query');
        if ($scope.query){$scope.perform_search(false)}
    }
    catch(e){
        $scope.query = '';
    }

    $scope.open_patient_info = function (event_id) {
        $window.sessionStorage.setItem('query', JSON.stringify($scope.query));
        $window.open(Config.url.ambulance_patient_info + '?event_id=' + event_id, '_self');
    };

    $scope.onPageChanged = function () {
        $scope.perform_search(true);
    };
};
