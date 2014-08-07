var ScheduleDayCtrl = function ($scope, $http, $modal, $filter, WMClient, PrintingService, $interval, WMAppointmentDialog, $location, $anchorScroll) {
    $scope.client_id = null;
    $scope.client = null;
//    $scope.show_past_tickets = false;

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
                $scope.person = data.result.person;
                $scope.show_past_tickets = false;
            });
    };

    $scope.dateChanged = function () {
        $scope.loadData();
    };

    $scope.today = function () {
        $scope.date = new Date();
        $scope.dateChanged();
    };
    $scope.today();

    $scope.show_time = function (date_time) {
        return moment(date_time).isAfter(moment().subtract(1, 'hours'));
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
                    $location.hash('client_top');
                    $anchorScroll();
                });
            $scope.client.reload('for_servicing');
        } else if ($scope.client) {
            var instance;
            if (ticket.status != 'busy') {
                instance = WMAppointmentDialog.make(ticket, $scope.person, $scope.client.info.id, $scope.client.info.full_name);
            }
            instance.result.then(function () {
                $scope.client.reload('for_servicing');
                $scope.loadData();
            })
        }
    };
    $scope.ps_amb = new PrintingService('preliminary_records');
    $scope.ps_amb.set_context('orderAmb');
    $scope.ps_amb_resolve = function (client_ticket_id) {
        return {
            client_id: $scope.client.client_id,
            ticket_id: client_ticket_id
        }
    };
    $scope.ps_home = new PrintingService('preliminary_records');
    $scope.ps_home.set_context('orderHome');
    $scope.ps_home_resolve = function (client_ticket_id) {
        return {
            client_id: $scope.client.client_id,
            ticket_id: client_ticket_id
        }
    };

    $scope.new_event = function(client_id, ticket_id) {
        var query = '?client_id=' + client_id;
        if (ticket_id){
            query += '&ticket_id=' + ticket_id;
        }
        $scope.child_window = window.open(url_event_new_event_html + query, '_blank');
    };

    $scope.open_event = function(event_id) {
        $scope.child_window = window.open(url_for_event_html_event_info + '?event_id=' + event_id, '_blank');
    };

    $scope.new_appointment = function(client_id) {
        $scope.child_window = window.open(url_schedule_appointment_html + '?client_id=' + client_id, '_blank');
    };

    var interval;
    $scope.clearInterval = function() {
        $interval.cancel(interval);
        interval = undefined;
    };

    $scope.$watch('child_window.document', function (n, o) {
        if (n && n!=o) {
            $scope.clearInterval();
            interval = $interval(function () {
                if ($scope.child_window.closed) {
                    $scope.client.reload('for_servicing');
                    $scope.clearInterval();
                    $scope.child_window = {};
                }
            }, 500);
        }
    });
};
WebMis20.controller('ScheduleDayCtrl', ['$scope', '$http', '$modal', '$filter', 'WMClient', 'PrintingService', '$interval', 'WMAppointmentDialog', '$location', '$anchorScroll', ScheduleDayCtrl]);
