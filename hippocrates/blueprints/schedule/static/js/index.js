/**
 * Created by mmalkov on 11.07.14.
 */
var ScheduleCtrl = function ($scope, $http, $window, $location, RefBook, PersonTreeUpdater, WMAppointmentDialog,
                             PrintingService, PrintingDialog, MessageBox, CurrentUser) {
    $scope.aux = aux;
    var params = aux.getQueryParams();
    $scope.person_id = params.person_id || CurrentUser.info.id;
    $scope.person_query = '';
    var curDate = new Date();
    var curYear = curDate.getUTCFullYear();
    var curMonth = curDate.getMonth();
    $scope.years = [curYear - 1, curYear, curYear + 1];
    $scope.year = curYear;
    $scope.month = curMonth;
    $scope.reception_types = new RefBook('rbReceptionType');
    $scope.reception_type = 'amb';
    $scope.ps = new PrintingService('schedule');

    $scope.get_ps_resolve = function () {
        return {
            person_id: $scope.person_id
        }
    };
    $scope.openPrintDialog = function (period) {
        var start_date = null,
            end_date = null;
        if (period === 'today') {
            start_date = new Date();
            end_date = moment().add(1, 'd').toDate();
        } else if (period === 'week') {
            start_date = $scope.pages[$scope.page].toDate();
            end_date = moment($scope.pages[$scope.page]).add(7, 'd').toDate();
        } else if (period === 'month') {
            start_date = new Date($scope.year, $scope.month, 1);
            end_date = moment(start_date).add(1, 'M').toDate();
        }
        function processPrint() {
            PrintingDialog.open($scope.ps, $scope.get_ps_resolve(), {
                start_date: start_date,
                end_date: end_date
            }, true);
        }

        if (!$scope.ps.is_loaded()) {
            $scope.ps.set_context('scheduleQueue')
                .then(function () {
                    processPrint();
                }, function () {
                    MessageBox.error(
                        'Печать недоступна',
                        'Сервис печати недоступен. Свяжитесь с администратором.'
                    );
                });
        } else {
            processPrint();
        }
    };

    $scope.reloadSchedule = function () {
        var forced = arguments[0] === true;
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
                if (forced) {
                    var path = $location.path() + '?person_id=' + d.person.id;
                    $location.url(path).replace();
                    //history.pushState({
                    //    person_id: $scope.person_id,
                    //    pages: $scope.pages,
                    //    person: $scope.person,
                    //    grouped: $scope.grouped,
                    //    year: $scope.year,
                    //    month: $scope.month,
                    //    page: $scope.page
                    //}, null, window.location.origin + window.location.pathname + '?person_id=' + d.person.id);
                }
            });
        }
    };

    $scope.setDatePage = function (index) {
        if (index != $scope.page) {
            $scope.page = index;
            $scope.reloadSchedule();
            $scope.update_sched_in_person_tree($scope.pages[$scope.page]);
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
        var end_date = moment(start_date).endOf('month');
        start_date = start_date.subtract(start_date.isoWeekday() - 1, 'days');
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
        $scope.update_sched_in_person_tree($scope.pages[$scope.page]);
    };

    $scope.update_sched_in_person_tree = function (start_date) {
        PersonTreeUpdater.set_schedule_period(
            start_date.clone().toDate(),
            start_date.clone().add(6, 'd').endOf('day').toDate()
        );
    };

    $scope.changeReceptionType = function (code) {
        $scope.reception_type = code;
    };

    $scope.monthChanged();

    $scope.$watch('person_id', function (new_value, old_value) {
        if (!new_value) return;
        $scope.reloadSchedule(true);
    });

    $scope.ticket_user_info_available = function (ticket) {
        return ticket && ticket.record && ticket.record.client_id;
    };

    $scope.view_patient_info = function (ticket) {
        var url = CurrentUser.current_role_in('admin', 'clinicRegistrator') ?
            url_client_html :
            url_for_patien_info_full;
        url += '?client_id=' + ticket.record.client_id;
        $window.open(url);
    };

    $scope.appointment_toggle = function (ticket) {
        var instance;
        if (ticket.status == 'busy') {
            instance = WMAppointmentDialog.cancel(ticket, $scope.person, ticket.record.client_id);
        } else {
            instance = WMAppointmentDialog.make(ticket, $scope.person, null);
        }
        instance.result.then(function () {
            $scope.reloadSchedule();
        });
    };

    //window.onpopstate = function (event) {
    //    // Это всё происходит вне контекста скоупа, и потому не запускается вотчер на person_id, иначе нам пришлось
    //    // бы делать хак
    //    if (event.state) {
    //        $scope.person_id = event.state.person_id;
    //        $scope.pages = event.state.pages;
    //        $scope.person = event.state.person;
    //        $scope.grouped = event.state.grouped;
    //        $scope.year = event.state.year;
    //        $scope.month = event.state.month;
    //        $scope.page = event.state.page;
    //    } else {
    //        $scope.person_id = undefined;
    //        $scope.pages = [];
    //        $scope.person = undefined;
    //        $scope.grouped = undefined;
    //        $scope.year = curYear;
    //        $scope.month = curDate.getMonth();
    //        $scope.page = -1;
    //    }
    //    $scope.$digest();
    //}
};
WebMis20.controller('ScheduleCtrl', ['$scope', '$http', '$window', '$location', 'RefBook', 'PersonTreeUpdater',
    'WMAppointmentDialog', 'PrintingService', 'PrintingDialog', 'MessageBox', 'CurrentUser', ScheduleCtrl]);
