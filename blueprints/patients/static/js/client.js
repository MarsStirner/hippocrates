'use strict';

angular.module('WebMis20.controllers').
    controller('ClientCtrl',
        ['$scope', '$http', '$modal', 'WMClient', 'WMClientServices', 'PrintingService', 'RefBookService', '$window', '$document',
        function ($scope, $http, $modal, WMClient, WMClientServices, PrintingService, RefBookService, $window, $document) {
            $scope.records = [];
            $scope.aux = aux;
            $scope.params = aux.getQueryParams(document.location.search);
            $scope.rbGender = RefBookService.get('Gender');
            $scope.rbPerson = RefBookService.get('vrbPersonWithSpeciality');
            $scope.alerts = [];
            $scope.clientServices = WMClientServices;

            $scope.currentDate= new Date();

            $scope.client_id = $scope.params.client_id;
            var client = $scope.client = new WMClient($scope.client_id);

            $scope.editing = {
                submit_attempt: false
            };

            // printing stuff
            $scope.ps = new PrintingService('registry');
            $scope.print_context_resolve = function () {
                return {
                    client_id: $scope.client_id
                }
            };
            $scope.ps.set_context('token');
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
            $scope.$on('printing_error', function (event, error) {
                $scope.alerts.push(error);
            });
            // printing stuff end

            $scope.$watch('mainInfoForm.$dirty', function(n, o) {
                if (n !== o) {
                    client.info.dirty = n;
                }
            });

            $scope.bt_history_visible = function() {
                return client.blood_types && client.blood_types.filter(function(el) {
                    return el.id;
                }).length > 1;
            };

            $scope.save_client = function() {
                var form = $scope.clientForm;
                $scope.editing.submit_attempt = true;
                if (form.$invalid) {
                    var formelm = $('#clientForm').find('.ng-invalid:first');
                    $document.scrollToElement(formelm, 30, 1500);
                    return false;
                }
                $scope.client.save().then(function(new_client_id) {
                    if ($scope.client_id == 'new') {
                        $scope.clientForm.$setPristine();
                        window.open(url_client_html + '?client_id=' + new_client_id, '_self');
                    } else {
                        $scope.client.reload().then(function() {
                            $scope.refresh_form();
                        }, function() {
                            // todo: onerror?
                        });
                    }
                }, function(message) {
                    alert(message);
                });
            };

            $scope.cancel_editing = function() {
                if (window.opener) {
                    window.opener.focus();
                    window.close();
                } else {
                    history.back();
                }
            };

            $scope.refresh_form = function() {
                $scope.mainInfoForm.$setPristine(true);
                if (!client.reg_addresses.length) {
                    $scope.clientServices.push_address(client, 0);
                }
                if (!client.live_addresses.length) {
                    $scope.clientServices.push_address(client, 1);
                }
                if (!client.compulsory_policies.length) {
                    $scope.clientServices.add_new_cpolicy(client);
                }
                if (!client.id_docs.length) {
                    $scope.clientServices.add_id_doc(client);
                }
            };

            client.reload().then(function() {
                $scope.refresh_form();
            }, function(message) {
                alert(message);
            });
        }
    ]);