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
var ClientModalCtrl = function ($scope, $modalInstance, client, PrintingService, $modal, $interval) {
    $scope.current_user = current_user;
    $scope.client = client;
    $scope.client_id = client.client_id;
    $scope.child_window = {};
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

    $scope.new_event = function(client_id, ticket_id) {
        var query = '?client_id=' + client_id;
        if (ticket_id){
            query += '&ticket_id=' + ticket_id;
        }
        $scope.child_window = window.open(url_event_new_event_html + query, '_blank');
    };

    $scope.new_appointment = function(client_id) {
        $scope.child_window = window.open(url_schedule_appointment_html + '?client_id=' + client_id, '_blank');
    };

    $scope.open_event = function(event_id) {
        $scope.child_window = window.open(url_for_event_html_event_info + '?event_id=' + event_id, '_blank');
    };

    $scope.open_client = function (client_id) {
        $scope.child_window = window.open(url_client_html + '?client_id=' + client_id, '_blank');
    };

    $scope.modal_create_event = function() {
        var modalInstance = $modal.open({
            templateUrl: 'modal-createEvent.html',
            controller: CreateEventModalCtrl
        });
        modalInstance.result.then(function (accept) {
            if (accept) {
                $scope.new_event($scope.client_id)
            }
        })
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

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

    $modalInstance.result.then(function () {
        $scope.client = null;
    }, function () {
        $scope.client = null;
    });
};
var ClientSearch = function ($scope, WMClient, $modal) {
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
        var modalInstance = $modal.open({
            templateUrl: 'modal-client.html',
            resolve: {
                client: function () {
                    return $scope.client;
                }
            },
            controller: ClientModalCtrl,
            size: 'lg'
        });
    };
};
WebMis20.controller('ClientSearch', ['$scope', 'WMClient', '$modal', ClientSearch]);
