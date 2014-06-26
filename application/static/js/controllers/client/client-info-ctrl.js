'use strict';

angular.module('WebMis20.controllers').
    controller('ClientCtrl', ['$scope', '$http', '$modal', 'WMClient', 'PrintingService', 'RefBookService', '$window',
        function ($scope, $http, $modal, WMClient, PrintingService, RefBookService, $window) {
            $scope.records = [];
            $scope.aux = aux;
            $scope.params = aux.getQueryParams(document.location.search);
            $scope.rbGender = RefBookService.get('Gender');
            $scope.rbPerson = RefBookService.get('vrbPersonWithSpeciality');
            $scope.alerts = [];

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

            $scope.flt_not_deleted = function() {
                return function(item) {
                    return item.hasOwnProperty('deleted') ? item.deleted === 0 : true;
                };
            }; // TODO: application level

            $scope.$watch('mainInfoForm.$dirty', function(n, o) {
                if (n !== o) {
                    client.info.dirty = n;
                }
            });

            $scope.delete_document = function(entity, doc) {
                if (confirm('Документ будет удален. Продолжить?')) {
                    client.delete_record(entity, doc);
                    client.add_id_doc();
                }
            };

            $scope.add_new_cpolicy = function() {
                var cpols = client.compulsory_policies.filter(function(p) {
                    return p.deleted === 0;
                });
                var cur_cpol = cpols[cpols.length - 1];
                if (cpols.length) {
                    var msg = [
                        'При добавлении нового полиса ОМС старый полис будет удален',
                        cur_cpol.id ? ' и станет доступен для просмотра в истории документов' : '',
                        '. Продолжить?'
                    ].join('');
                    if (confirm(msg)) {
                        client.delete_record('compulsory_policies', cur_cpol, 2);
                        client.add_cpolicy();
                    }
                } else {
                    client.add_cpolicy();
                }
            };

            $scope.delete_policy = function(entity, policy) {
                if (confirm('Полис будет удален. Продолжить?')) {
                    client.delete_record(entity, policy);
                }
            };

            $scope.add_new_blood_type = function(person_id) {
                var bt = client.blood_types;
                if (bt.length && !bt[0].id) {
                    bt.splice(0, 1);
                }
                client.add_blood_type();
                bt[0].person = $scope.rbPerson.get(person_id);
            };

            $scope.delete_blood_type = function(bt) {
                client.delete_record('blood_types', bt);
            };

            $scope.bt_history_visible = function() {
                return client.blood_types && client.blood_types.filter(function(el) {
                    return el.id;
                }).length > 1;
            };

            $scope.delete_address = function(entity, addr) {
                if (confirm('Адрес будет удален. Продолжить?')) {
                    client.delete_record(entity, addr);
                }
            };

            $scope.get_actual_reg_address = function() {
                var addrs =  client.reg_addresses.filter(function(el) {
                    return el.deleted === 0;
                });
                return addrs.length === 1 ? addrs[0] : null;
            };

            $scope.add_new_address = function(entity, addr_type) {
                var addrs = client[entity].filter(function(el) {
                    return el.deleted === 0;
                });
                var cur_addr = addrs[addrs.length - 1];
                if (addrs.length) {
                    var msg = [
                        'При добавлении нового адреса старый адрес будет удален',
                        cur_addr.id ? ' и станет доступен для просмотра в истории' : '',
                        '. Продолжить?'
                    ].join('');
                    if (confirm(msg)) {
                        client.delete_record(entity, cur_addr, 2);
                        client.add_address(addr_type);
                    }
                } else {
                    client.add_address(addr_type);
                }
            };

            $scope.save_client = function() {
                var form = $scope.clientForm;
                $scope.editing.submit_attempt = true;
                if (form.$invalid) {
                    return false;
                }
                $scope.client.save().then(function(new_client_id) {
                    if ($scope.client_id == 'new') {
                        window.open(url_client_html + '?client_id=' + new_client_id, '_self');
                    } else {
                        $scope.client.reload().then(function() {
                            $scope.refresh_form();
                        }, function() {
                            // todo: onerror?
                        });
                    }
                }, function(reason) {
                    alert(reason);
                });
            };

            $scope.refresh_form = function() {
                $scope.mainInfoForm.$setPristine(true);
                if (!client.reg_addresses.length) {
                    client.add_address(0);
                }
                if (!client.live_addresses.length) {
                    client.add_address(1);
                }
                if (!client.compulsory_policies.length) {
                    client.add_cpolicy();
                }
                if (!client.id_docs.length) {
                    client.add_id_doc();
                }
            };

            client.reload().then(function() {
                $scope.refresh_form();
            }, function() {
                // todo: onerror?
            });

//            $scope.delete_record = function(entity, record) {
//                var modalInstance = $modal.open({
//                    templateUrl: 'modal-deleteRecord.html',
//                    controller: DeleteRecordModalCtrl
//                });
//
//                modalInstance.result.then(function () {
//                    $scope.client.delete_record(entity, record);
//                });
//            };
        }
    ]);