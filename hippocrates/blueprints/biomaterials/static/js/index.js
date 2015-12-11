var IndexCtrl = function ($scope, $modal, $http, PrintingService) {
    $scope.search_date = {execDate:new Date()};
    $scope.get_data = function() {
        $http.get(url_get_ttj_records, {
            params: {
                execDate: $scope.search_date.execDate
            }
        })
        .then(function (res) {
                $scope.ttj_records = res.data.result;
        });
    };
    $scope.$watch('search_date.execDate', function (new_value, old_value) {
        $scope.get_data();
    });
};
