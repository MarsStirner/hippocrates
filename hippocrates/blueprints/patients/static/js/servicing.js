/**
 * Created by mmalkov on 11.07.14.
 */
var CreateEventModalCtrl = function ($scope, $modalInstance) {
    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
    $scope.accept = function () {
        $modalInstance.close(true);
    };
};
var ClientModalCtrl = function ($scope, $modalInstance, $filter, $modal, $window,
                                PrintingService, WMWindowSync, client, WMConfig, localStorageService) {
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
    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
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
    $scope.new_event = function(client_id, ticket_id) {
        var query = '?client_id=' + client_id;
        if (ticket_id) {
            query += '&ticket_id=' + ticket_id;
        }
        var url = WMConfig.url.event.html.request_type_kind + query;
        $window.open(url);
    };

    $scope.new_appointment = function(client_id) {
        var url = WMConfig.url.schedule.html.appointment + '?client_id=' + client_id;
        WMWindowSync.openTab(url, $scope.reload_client);
    };

    $scope.open_event = function(event_id) {
        var url = WMConfig.url.event.html.event_info + '?event_id=' + event_id;
        $window.open(url);
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

    $scope.create_stationary_event = function (client_id) {
        var url = WMConfig.url.webmis_1_0.create_event.format(client_id);
        WMWindowSync.openTab(url, $scope.reload_client);
    };
    $scope.reload_client = function () {
        if ($scope.client) {
            $scope.client.reload('for_servicing');
        }
    };
    $scope.openPatientActions = function () {
        $scope.$broadcast('patientActionsOpened', {client_id: $scope.client_id});
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

    $scope.$on('LocalStorageModule.notification.changed', function() {
        var modalClientToUpdate = localStorageService.get('modalClientToUpdate') || {};
        if(modalClientToUpdate.hasOwnProperty($scope.client.info.id)) {
            $scope.reload_client();
        }
    });

    $modalInstance.result.then(function () {
        $scope.client = null;
    }, function () {
        $scope.client = null;
    });
};

var ClientSearch = function ($scope, WMClient, $modal, CurrentUser) {
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.query = "";
    $scope.client_id = null;
    $scope.client = null;

    $scope.set_patient_id = function (selected_client) {
        var patient_id = selected_client.info.id;
        $scope.client_id = patient_id;
        $scope.client = new WMClient(patient_id);
        $scope.client.reload('for_servicing');
    };

    $scope.$watch('client.info.id', function(n, o){
        if (n && o != n) {
            $scope.modal_client();
        }
    });

    $scope.modal_client = function() {
        var template = CurrentUser.current_role_in('admNurse') ?
            'modal-client-cut.html' :
            'modal-client.html';
        var modalInstance = $modal.open({
            templateUrl: template,
            backdrop : 'static',
            resolve: {
                client: function () {
                    return $scope.client;
                }
            },
            controller: ClientModalCtrl,
            size: 'lg',
            windowClass: 'modal-scrollable'
        });
    };
};
WebMis20.controller('ClientSearch', ['$scope', 'WMClient', '$modal', 'CurrentUser', ClientSearch]);
WebMis20.controller('ClientModalCtrl', ['$scope', '$modalInstance', '$filter', '$modal', '$window', 'PrintingService',
    'WMWindowSync', 'client', 'WMConfig', 'localStorageService', ClientModalCtrl]);

