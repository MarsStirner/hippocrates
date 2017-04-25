'use strict';

var ClientSearchModalCtrl = function ($scope, $filter, PrintingService,
        WMWindowSync, WMConfig, MessageBox, CurrentUser, EventModalService,
        PatientModalService, client) {
    $scope.client = client;
    $scope.client_id = client.client_id;
    $scope.event = client.current_hosp;
    $scope.alerts = [];

    $scope.ps = new PrintingService('registry');
    $scope.ps_resolve = function () {
        return {
            client_id: $scope.client_id
        }
    };
    $scope.ps_amb = new PrintingService('preliminary_records');
    $scope.ps_amb_resolve = function (client_ticket_id) {
        return {
            client_id: $scope.client_id,
            ticket_id: client_ticket_id
        }
    };
    $scope.ps_home = new PrintingService('preliminary_records');
    $scope.ps_home_resolve = function (client_ticket_id) {
        return {
            client_id: $scope.client_id,
            ticket_id: client_ticket_id
        }
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
    $scope.newEvent = function (ticket_id) {
        var url = WMConfig.url.event.html.request_type_kind + '?client_id=' + $scope.client_id;
        if (ticket_id) {
            url += '&ticket_id=' + ticket_id;
        }
        WMWindowSync.openTab(url, $scope.reload_client);
    };
    $scope.newEventChecked = function(ticket_id) {
        if ($scope.client.appointments.length > 0 &&
                !CurrentUser.current_role_in('clinicDoctor')) {
            MessageBox.question(
                'У пациента есть предварительные записи',
                'Если пациент обратился на основе предварительной записи, то ' +
                'создание нового обращения следует производить путём нажатия на ' +
                'кнопку <span class="btn btn-xs btn-success">' +
                '<span class="glyphicon glyphicon-plus"></span></span> в ' +
                'соответствующей строке в таблице предварительных записей.<br><br>' +
                'Всё равно продолжить?'
            ).then(function () {
                $scope.newEvent(ticket_id);
            });
        } else {
            $scope.newEvent(ticket_id);
        }
    };

    $scope.newAppointment = function() {
        var url = WMConfig.url.schedule.html.appointment + '?client_id=' + $scope.client_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.openEvent = function(event_id) {
        var url = WMConfig.url.event.html.event_info + '?event_id=' + event_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.openClient = function () {
        var url = WMConfig.url.patients.client_html + '?client_id=' + $scope.client_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };
    $scope.openClientModal = function () {
        var copy = $scope.client.clone();
        PatientModalService.openClient(copy, true)
            .then(function (edited_client) {
                $scope.reload_client();
            });
    };
    $scope.createHospitalisation = function () {
        EventModalService.openNewHospitalisation($scope.client_id)
            .then(function (edited_hosp) {
                $scope.reload_client();
            });
    };
    $scope.editHospitalisation = function () {
        var hosp = $scope.client.current_hosp.clone();
        EventModalService.openEditHospitalisation(hosp)
            .then(function (edited_hosp) {
                $scope.reload_client();
            });
    };
    $scope.curHospAvailable = function () {
        return $scope.client.current_hosp;
    };
    $scope.reload_client = function () {
        $scope.client.reload('for_servicing');
    };
    $scope.openPatientActions = function () {
        $scope.$broadcast('patientActionsOpened', {client_id: $scope.client_id});
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });
};


WebMis20.controller('ClientSearchModalCtrl', ['$scope', '$filter', 'PrintingService',
    'WMWindowSync', 'WMConfig', 'MessageBox', 'CurrentUser', 'EventModalService',
    'PatientModalService', ClientSearchModalCtrl]);
