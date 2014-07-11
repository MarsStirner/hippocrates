/**
 * Created by mmalkov on 11.07.14.
 */
var PersonAppointmentCtrl = function ($scope, $http, RefBook, WMAppointmentDialog) {
    $scope.modal = {};
    $scope.max_tickets = [];
    $scope.person_schedules = [];
    $scope.user_schedules = [];
    $scope.total_schedules = [];

    $scope.user_selected = [];
    $scope.data_selected = [];
    $scope.foldedArray = [];

    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.client_id = $scope.params.client_id;
    var curDate = new Date();
    var curYear = curDate.getUTCFullYear();
    $scope.years = [curYear - 1, curYear, curYear + 1];
    $scope.year = curYear;

    $scope.month = curDate.getMonth();

    $scope.reception_types = new RefBook('rbReceptionType');
    $scope.reception_type = 'amb';

    $scope.setDatePage = function(index) {
        if (index != $scope.page) {
            $scope.page = index;
            $scope.loadData();
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
        $scope.loadData();
    };

    $scope.changeReceptionType = function (code) {
        $scope.reception_type = code;
    };

    $scope.loadData = function () {
        $http.get(
            url_schedule_api_schedule, {
                params: {
                    client_id: $scope.client_id,
                    start_date: $scope.pages[$scope.page].format('YYYY-MM-DD'),
                    related: true,
                    person_ids: '[' + $scope.user_selected.join() + ']'
                }
            }
        ).success(function (data) {
                $scope.person_schedules = data.result.related_schedules;
                $scope.user_schedules = data.result.schedules;
                $scope.data_selected = data.result.related_schedules.map(function (item) {
                    return item.person.id;
                });
                $scope.refreshSchedules();
            });
    };

    $scope.refreshSchedules = function () {
        $scope.total_schedules = [].concat($scope.person_schedules, $scope.user_schedules).sort(function compare(a, b) {
            if (a.person.name < b.person.name)
                return -1;
            else if (a.person.name > b.person.name)
                return 1;
            return 0;
        }).map(function fold(person_schedule) {
            if ($scope.is_folded(person_schedule.person.id)) {
                return {
                    person: person_schedule.person,
                    grouped: aux.forEach(person_schedule.grouped, function (grouped_schedule) {
                        var max_tickets = 0;
                        var schedule = grouped_schedule.schedule.map(function (day) {
                            var result = {
                                date: day.date,
                                tickets: day.tickets.filter(function (ticket) {return ticket.client != null;})
                            };
                            max_tickets = Math.max(max_tickets, result.tickets.length);
                            return result;
                        });
                        return {
                            max_tickets: max_tickets,
                            schedule: schedule
                        }
                    })
                }
            } else {
                return person_schedule;
            }
        });
    };
    $scope.appointment_toggle = function (ticket, person) {
        var instance;
        if (ticket.status == 'busy') {
            instance = WMAppointmentDialog.cancel(ticket, person, $scope.client_id)
        } else {
            instance = WMAppointmentDialog.make(ticket, person, $scope.client_id)
        }
        instance.result.then(function () {
            $scope.loadData();
        })
    };

    $scope.is_folded = function (person_id) {
        return aux.inArray($scope.foldedArray, person_id);
    };

    $scope.person_fold = function (person_id) {
        $scope.foldedArray.push(person_id);
        $scope.refreshSchedules();
    };

    $scope.person_unfold = function (person_id) {
        var index = $scope.foldedArray.indexOf(person_id);
        $scope.foldedArray.splice(index, 1);
        $scope.refreshSchedules();
    };

    $scope.$watch('user_selected', function (new_value, old_value) {
        var new_ids = new_value.filter(aux.func_not_in(old_value));
        if (new_ids.length) {
            $http.get(url_schedule_api_schedule, {
                params: {
                    client_id: $scope.client_id,
                    person_ids: new_ids[0],
                    start_date: $scope.pages[$scope.page].format('YYYY-MM-DD')
                }
            }).success(function (data) {
                $scope.user_schedules.push(data.result['schedules'][0]);
                $scope.refreshSchedules();
            })
        } else {
            var del_ids = old_value.filter(aux.func_not_in(new_value));
            if (del_ids.length) {
                var del_id = del_ids[0];
                $scope.user_schedules = $scope.user_schedules.filter(function (sched_group) {
                    return sched_group.person.id != del_id;
                });
                $scope.refreshSchedules();
            }
        }
    });

    $scope.monthChanged();
};
WebMis20.controller('PersonAppointmentCtrl', ['$scope', '$http' , 'RefBook', 'WMAppointmentDialog', PersonAppointmentCtrl]);
