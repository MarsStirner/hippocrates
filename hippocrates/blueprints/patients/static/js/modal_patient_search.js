'use strict';

//WebMis20.run(['$templateCache', '$http', function ($templateCache, $http) {
//    $http.get('/patients/static/templates/modal_patient_search.html').then(function(response) {
//        $templateCache.put('/WebMis20/modal/patients/patient_search.html', response.data);
//    });
//}]);


var CreateEventModalCtrl = function ($scope, $modalInstance) {
    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
    $scope.accept = function () {
        $modalInstance.close(true);
    };
};


var ClientSearchModalCtrl = function ($scope, $filter, $modal, PrintingService, WMWindowSync, WMConfig, client) {
    $scope.client = client;
    $scope.client_id = client.client_id;
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
    $scope.ps_amb.set_context('orderAmb');
    $scope.ps_home.set_context('orderHome');
    $scope.ps.set_context('token');

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
    $scope.new_event = function(client_id, ticket_id) {
        var query = '?client_id=' + client_id;
        if (ticket_id) {
            query += '&ticket_id=' + ticket_id;
        }
        var url = WMConfig.url.event.html.request_type_kind + query;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.new_appointment = function(client_id) {
        var url = WMConfig.url.schedule.html.appointment + '?client_id=' + client_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.open_event = function(event_id) {
        var url = WMConfig.url.event.html.event_info + '?event_id=' + event_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.open_client = function (client_id) {
        var url = WMConfig.url.patients.client_html + '?client_id=' + client_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.modal_create_event = function() {
        var modalInstance = $modal.open({
            templateUrl: 'modal-createEvent.html',
            backdrop : 'static',
            controller: CreateEventModalCtrl
        });
        modalInstance.result.then(function (accept) {
            if (accept) {
                $scope.new_event($scope.client_id)
            }
        })
    };

    $scope.createHospEvent = function (client_id) {
        var url = WMConfig.url.webmis_1_0.create_event.format(client_id);
        WMWindowSync.openTab(url, $scope.reload_client);
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


WebMis20.controller('ClientSearchModalCtrl', ['$scope', '$filter', '$modal', 'PrintingService', 'WMWindowSync',
    'WMConfig', ClientSearchModalCtrl]);