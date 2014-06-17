'use strict';

angular.module('WebMis20.controllers').
    controller('ClientCtrl', ['$scope', '$http', '$modal', 'WMClient', 'PrintingService', 'RefBookService', '$window',
        function ($scope, $http, $modal, WMClient, PrintingService, RefBookService, $window) {
            $scope.records = [];
            $scope.aux = aux;
            $scope.params = aux.getQueryParams(document.location.search);
            $scope.rbGender = RefBookService.get('Gender'); // {{ Enum.get_class_by_name('Gender').rb() | tojson }};
//            $scope.rbDocumentType = RefBookService.get('rbDocumentType');
//            $scope.rbUFMS = RefBookService.get('rbUFMS');
//            $scope.rbPolicyType = RefBookService.get('rbPolicyType');
//            $scope.rbOrganisation = RefBookService.get('Organisation');
            $scope.rbRelationType = RefBookService.get('rbRelationType');
            $scope.client_id = $scope.params.client_id;
            var client = $scope.client = new WMClient($scope.client_id);
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

            $scope.alerts = [];
            $scope.editing = {
                active: true,
                submit_attempt: false
            };

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

            $scope.flt_not_deleted = function() {
                return function(item) {
                    return item.deleted === 0;
                };
            };

            $scope.directRelationFilter = function (relationType) {
                return (relationType.leftSex == 0 || relationType.leftSex == $scope.client.client_info.sex.id);
            };

            $scope.reversedRelationFilter = function (relationType) {
                return (relationType.rightSex == 0 || relationType.rightSex == $scope.client.client_info.sex.id);
            };

            $scope.start_editing = function() {
                $scope.editing.active = true;
            };

            $scope.cancel_editing = function() {
                if ($scope.client_id == 'new') {
                    $window.history.back();
                } else {
                    $scope.editing.active = false;
                    $scope.client.reload();
                }
            };

            $scope.editing_is_active = function() {
                return $scope.editing.active || true;
            };

            $scope.save_client = function(form) {
                $scope.editing.submit_attempt = true;
                if (form.$invalid) {
                    return false;
                }
                $scope.client.save().then(function(new_client_id) {
                    if ($scope.client_id == 'new') {
                        window.open(url_client_html + '?client_id=' + new_client_id, '_self');
                    } else {
                        $scope.client.reload();
                    }
                }, function(reason) {
                    alert(reason);
                });
            };

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

            $scope.$on('printing_error', function (event, error) {
                $scope.alerts.push(error);
            });

            $scope.copy_address = function(state, addr_from) {
                // fixme: как бы эту штуку связать с директивами, как изначально задумывалось...
                // и тут есть баг, который надо фиксить, переделав все это
                if (!state) {
                    $scope.client.client_info.liveAddress = angular.copy(addr_from);
                    $scope.client.client_info.liveAddress.same_as_reg = true;
                } else {
                    $scope.client.client_info.liveAddress = {};
                    $scope.client.client_info.liveAddress.same_as_reg = false;
                }
            };

            $scope.initialize = function() {
                client.reload().then(function() {
                    if (!client.compulsory_policies.length) {
                        client.add_cpolicy();
                    }
                    if (!client.id_docs.length) {
                        client.add_id_doc();
                    }
                }, function() {
                    // todo: onerror?
                });
            };

            $scope.initialize();
        }
    ]);