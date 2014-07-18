var ScheduleDayCtrl = function ($scope, $http, $modal, $filter, WMClient) {
    $scope.client_id = null;
    $scope.client = null;
    $scope.today = function () {
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
    $scope.ticket_choose = function (ticket) {
        if (ticket.record && ticket.record.client_id) {
            $scope.ticket = ticket;
            $scope.event_id = ticket.record.event_id;
            $scope.client = new WMClient(ticket.record.client_id);
            $scope.client.reload('for_event').
                then(function() {
                    $scope.client.policies = [];
                    if ($scope.client.info.birth_date) {
                        $scope.client.age = moment().diff(moment($scope.client.info.birth_date), 'years');
                    }
                    if ($scope.client.compulsory_policies && $scope.client.compulsory_policies[0].policy_text) {
                        $scope.client.policies.push($scope.client.compulsory_policies[0].policy_text + ' (' + $filter('asDate')($scope.client.compulsory_policies[0].beg_date) + '-' + $filter('asDate')($scope.client.compulsory_policies[0].end_date) + ')');
                    }
                    if ($scope.client.voluntary_policies.length > 0) {
                        angular.forEach($scope.client.voluntary_policies, function (value, key) {
                            $scope.client.policies.push(value.policy_text + ' (' + $filter('asDate')(value.beg_date) + '-' + $filter('asDate')(value.end_date) + ')');
                        });
                    }
                });
            $scope.client.reload('for_servicing');
        }
    };

    $scope.dateChanged();
};
WebMis20.controller('ScheduleDayCtrl', ['$scope', '$http', '$modal', '$filter', 'WMClient', ScheduleDayCtrl]);
