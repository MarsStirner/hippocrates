var ScheduleDayCtrl = function ($scope, $http, $modal, RefBook) {
    $scope.today = function() {
        $scope.date = new Date();
    };
    $scope.today();

    $scope.dateChanged = function () {
        $scope.loadData();
    };

    $scope.loadData = function () {
        $http.get(
            url_schedule_api_day_schedule, {
                params: {
                    person_id: current_user_id,
                    one_day: true,
                    start_date: moment($scope.date).format('YYYY-MM-DD')
                }
            }
        ).success(function (data) {
            $scope.schedules = data.result.schedules;
        });
    };

    $scope.dateChanged();
};
WebMis20.controller('ScheduleDayCtrl', ['$scope', '$http', '$modal', 'RefBook', ScheduleDayCtrl]);
