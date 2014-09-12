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
var ClientSearch = function ($scope, $http, $timeout, $window, PrintingService, WMClient, WMClientServices, $modal, $q) {
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.query = "";
    $scope.results = null;
    $scope.client_id = null;
    $scope.client = null;
    $scope.clientServices = WMClientServices;
    $scope.alerts = [];

    $scope.set_patient_id = function (patient_id) {
        $scope.client_id = patient_id;
        $scope.client = new WMClient(patient_id);
        $scope.client.reload('for_servicing');
    };

    $scope.clear_results = function () {
        $scope.results = null;
        $scope.client = null;
        $scope.client_id = null;
    };

    var canceler = $q.defer();
    $scope.perform_search = function () {
        canceler.resolve();
        canceler = $q.defer();
        if ($scope.query) {
            $http.get(
                url_client_search, {
                    params: {
                        q: $scope.query
                    },
                    timeout: canceler.promise
                }
            ).success(function (data) {
                    $scope.results = data.result;
                });
        }
    };

    $scope.query_clear = function () {
        $scope.query = '';
        $scope.clear_results();
    };

    $scope.$watch('client.info.id', function(n, o){
        if (n && o != n) {
            $scope.modal_client();
        }
    });

    $scope.open_client = function (client_id) {
        window.open(url_client_html + '?client_id=' + client_id, '_blank');
    };

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
WebMis20.controller('ClientSearch', ['$scope', '$http', '$timeout', '$window', 'PrintingService', 'WMClient', 'WMClientServices', '$modal', '$q', ClientSearch]);
