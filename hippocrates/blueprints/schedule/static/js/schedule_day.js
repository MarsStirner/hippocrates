var ScheduleDayCtrl = function ($scope, $http, $filter, $interval, $location, $anchorScroll, WMClient,
        PrintingService, WMAppointmentDialog, WMProcedureOffices, CurrentUser, WMConfig) {
    $scope.client_id = null;
    $scope.client = null;
    $scope.person = {};
    $scope.schedules = [];
    $scope.date = null;
    $scope.show_past_tickets = false;
    $scope.proc_offices = [];
    $scope.proc_office = { selected: null };
    $scope.ticket = null;
    $scope.event_id = null;

    $scope.modes = ['self_schedule', 'proc_office', 'full'];
    $scope.mode = $scope.modes[0];

    $scope.load_proc_offices = function () {
        WMProcedureOffices.get().then(function (po) {
            $scope.proc_offices = po;
        });
    };
    $scope.loadData = function () {
        var person_id = CurrentUser.get_main_user().id,
            proc_office_id = safe_traverse($scope.proc_office, ['selected', 'id']);
        $http.get(
            WMConfig.url.schedule.day_schedule, {
                params: {
                    person_id: person_id,
                    proc_office_id: proc_office_id,
                    one_day: true,
                    start_date: moment($scope.date).format('YYYY-MM-DD')
                }
            }
        ).success(function (data) {
            $scope.schedules = data.result.schedules;
            if (!$scope.person.id) {
                $scope.person = data.result.person;
            }
            $scope.show_past_tickets = false;
        });
    };

    $scope.dateChanged = function () {
        if ($scope.mode === 'proc_office' && !$scope.proc_office.selected) return;
        $scope.loadData();
    };
    $scope.procOfficeChanged = function () {
        $scope.loadData();
    };

    $scope.today = function () {
        $scope.date = new Date();
        $scope.dateChanged();
    };

    $scope.initialize = function () {
        if (CurrentUser.get_main_user().current_role === 'diagDoctor') {
            $scope.mode = $scope.modes[1];
            $scope.load_proc_offices();
        }
        $scope.today();
    };

    $scope.initialize();

    $scope.show_time = function (date_time) {
        return moment(date_time).isAfter(moment().subtract(1, 'hours'));
    };
    $scope.formatAppointmentDate = function (appointment) {
        return '{0}{ (|1|)}'.formatNonEmpty(
            appointment.attendance_type.code === 'planned' ?
                $filter('asDateTime')(appointment.begDateTime) :
                $filter('asDate')(appointment.begDateTime),
            appointment.attendance_type.code !== 'planned' ?
                appointment.attendance_type.name :
                null
        );
    };
    $scope.ticket_choose = function (ticket) {
        if (ticket.record && ticket.record.client_id) {
            $scope.ticket = ticket;
            $scope.event_id = ticket.record.event_id;
            $scope.client = new WMClient(ticket.record.client_id);
            $scope.client.reload('for_servicing').
                then(function() {
                    $location.hash('client_top');
                    $anchorScroll();
                    $scope.openPatientActions();
                });
        } else if ($scope.client) {
            var instance,
                person; // куда записывать - врач или кабинет
            if (ticket.status != 'busy') {
                if ($scope.mode === 'self_schedule') {
                    person = $scope.person;
                } else if ($scope.mode === 'proc_office') {
                    person = $scope.proc_office.selected;
                }
                instance = WMAppointmentDialog.make(ticket, person, $scope.client.info.id, $scope.client.info.full_name);
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
        $scope.child_window = window.open(WMConfig.url.event.html.request_type_kind + query, '_blank');
    };

    $scope.open_event = function(event_id) {
        $scope.child_window = window.open(WMConfig.url.event.html.event_info + '?event_id=' + event_id, '_blank');
    };

    $scope.new_appointment = function(client_id) {
        $scope.child_window = window.open(WMConfig.url.schedule.html.appointment + '?client_id=' + client_id, '_blank');
    };

    $scope.get_full_schedule_url = function () {
        var id_= $scope.mode === 'proc_office' ?
            safe_traverse($scope.proc_office, ['selected', 'id']) :
            $scope.person.id;
        if (id_) {
            return '{0}?person_id={1}'.format(WMConfig.url.schedule.html.index, id_);
        }
        return WMConfig.url.schedule.html.index;
    };

    $scope.openPatientActions = function () {
        $scope.$broadcast('patientActionsOpened', {client_id: $scope.client.client_id});
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
                    $scope.loadData();
                    $scope.clearInterval();
                    $scope.child_window = {};
                }
            }, 500);
        }
    });
};
WebMis20.controller('ScheduleDayCtrl', ['$scope', '$http', '$filter', '$interval', '$location', '$anchorScroll',
    'WMClient', 'PrintingService', 'WMAppointmentDialog', 'WMProcedureOffices', 'CurrentUser', 'WMConfig', ScheduleDayCtrl]);
