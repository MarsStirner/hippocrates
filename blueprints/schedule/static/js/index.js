/**
 * Created by mmalkov on 11.07.14.
 */
var ScheduleCtrl = function ($scope, $http, RefBook) {
    $scope.data = {};
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    // $scope.person_id = $scope.params.person_id;
    $scope.person_query = '';
    var curDate = new Date();
    var curYear = curDate.getUTCFullYear();
    $scope.years = [curYear - 1, curYear, curYear + 1];
    $scope.year = curYear;

    $scope.month = curDate.getMonth();

    $scope.reception_types = new RefBook('rbReceptionType');
    $scope.reception_type = 'amb';

    $scope.reloadSchedule = function () {
        if ($scope.person_id) {
            $http.get(
                url_schedule_api_schedule,
                {
                    params: {
                        person_ids: $scope.person_id,
                        start_date: $scope.pages[$scope.page].format('YYYY-MM-DD')
                    }
                }
            ).success(function (data) {
                    var d = data.result['schedules'][0];
                    $scope.person = d.person;
                    $scope.grouped = d.grouped;
                })
        }
    };

    $scope.setDatePage = function (index) {
        if (index != $scope.page) {
            $scope.page = index;
            $scope.reloadSchedule();
        }
    };

    $scope.monthChanged = function () {
        var mid_date = moment({
            year: $scope.year,
            month: $scope.month,
            day: new Date().getDate()
        });
        var start_date = moment({
            year: $scope.year,
            month: $scope.month,
            day: 1
        });
        var end_date = moment(start_date).add(1, 'M').subtract(1, 'd');
        var chosen_page = -1;
        var pages = [];
        while (start_date <= end_date) {
            if (mid_date >= start_date) {
                chosen_page += 1;
            }
            pages.push(moment(start_date));
            start_date.add(1, 'w');
        }
        $scope.page = chosen_page;
        $scope.pages = pages;
        $scope.reloadSchedule();
    };

    $scope.changeReceptionType = function (code) {
        $scope.reception_type = code;
    };

    $scope.monthChanged();

    $scope.$watch('person_id', function (new_value, old_value) {
        if (!new_value) return;
        history.pushState(null, null, window.location.origin + window.location.pathname + '?person_id=' + new_value);
        $scope.reloadSchedule();
    });
};
WebMis20.controller('ScheduleCtrl', ['$scope', '$http', 'RefBook', ScheduleCtrl]);
