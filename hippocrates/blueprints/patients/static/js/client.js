'use strict';

angular.module('WebMis20.controllers').
    controller('ClientCtrl',
        ['$scope', '$http', '$modal', 'WMClient', 'WMClientServices', 'PrintingService', 'RefBookService', '$window',
         '$document', 'FileEditModal', 'WMConfig', '$q', '$timeout',
        function ($scope, $http, $modal, WMClient, WMClientServices, PrintingService, RefBookService, $window, $document,
                  FileEditModal, WMConfig, $q, $timeout) {
            $scope.records = [];
            $scope.aux = aux;
            $scope.params = aux.getQueryParams(document.location.search);
            $scope.rbGender = RefBookService.get('Gender');
            $scope.alerts = [];
            $scope.clientServices = WMClientServices;
            $scope.currentDate = new Date();
            $scope.selected_files = [];

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
            $scope.btnAddSsDocVisible = function (socstat) {
                return safe_traverse(socstat, ['self_document', 'id']) === undefined;
            };
            $scope.btnClearSsDocVisible = function (socstat) {
                return safe_traverse(socstat, ['self_document', 'id']) === null;
            };

            $scope.save_client = function() {
                var form = $scope.clientForm;
                $scope.editing.submit_attempt = true;
                if (form.$invalid) {
                    var formelm = $('#clientForm').find('.ng-invalid:not(ng-form):first');
                    $document.scrollToElement(formelm, 100, 1500);
                    return false;
                }
                $scope.client.save().then(function(new_client_id) {
                    if ($scope.client_id == 'new') {
                        $scope.clientForm.$setPristine();
                        window.open(url_client_html + '?client_id=' + new_client_id, '_self');
                    } else {
                        $scope.reloadClient();
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

            $scope.reloadClient = function() {
                client.reload().then(function() {
                    $scope.refresh_form();
                }, function(message) {
                    alert(message);
                });
            };

            $scope.add_new_file = function (documentInfo, policyInfo) {
                FileEditModal.addNew($scope.client_id, {
                    attachType: 'client',
                    documentInfo: documentInfo,
                    policyInfo: policyInfo,
                    client: $scope.client
                })
                .then(function () {
                    $scope.reloadClient();
                }, function () {
                    $scope.reloadClient();
                });
            };
            $scope.openFile = function (cfa_id, idx) {
                FileEditModal.open(cfa_id, {
                    attachType: 'client',
                    idx: idx,
                    client: $scope.client,
                    editMode: true
                })
                .then(function () {
                    $scope.reloadClient();
                }, function () {
                    $scope.reloadClient();
                });
            };

            $scope.toggle_select_file = function (fa) {
                if($scope.selected_files.has(fa)) {
                    $scope.selected_files.remove(fa);
                } else {
                    $scope.selected_files.push(fa);
                }
            };

            $scope.select_all_files = function () {
                if ($scope.selected_files.length == client.file_attaches.length) {
                    $scope.selected_files = [];
                } else {
                    $scope.selected_files = client.file_attaches;
                }
            };

            $scope.printFilesAttach = function (fa_list) {
                function make_documents(fa_list) {
                    var deferred = $q.defer();
                    var html = '<html><style>{0}</style><body>{1}</body></html>'.format(
                        '@media print {\
                            img {\
                                max-width: 100% !important;\
                            }\
                        }',
                        '{0}'
                    );
                    var pages = [],
                        promises = [],
                        fidx=0;
                    angular.forEach(fa_list, function (fa) {
                        angular.forEach(fa.file_document.files, function (fileMeta) {
                            var idx = fileMeta.idx + fidx,
                                promise;
                            pages[idx] = new Image();
                            promise = $http.get(WMConfig.url.api_patient_file_attach, {
                                params: {
                                    file_meta_id: fileMeta.id
                                }
                            }).success(function (data) {
                                pages[idx].src = "data:{0};base64,".format(data.result.mime) + data.result.data;
                            }).error(function () {
                                pages[idx] = document.createElement('p');
                                pages[idx].innerHTML = 'Ошибка загрузки {0} страницы документа'.format(idx);
                            });
                            promises.push(promise);
                        });
                        ++fidx;
                    });

                    $q.all(promises).then(function composeDocument() {
                        var html_pages = '';
                        angular.forEach(pages, function (elem) {
                            html_pages += '<div style="page-break-after: always">{0}</div>'.format(elem.outerHTML)
                        });
                        html = html.format(html_pages);
                        deferred.resolve(html);
                    }, function () {
                        deferred.reject('Ошибка формирования документа на печать');
                    });
                    return deferred.promise;
                }
                // browser prevents opening a window if it was triggered not from user actions
                // i.e. user click event and corresponding callback function.
                // Using promises results in calling new functions, that are not directly fired by user.
                var w = $window.open();
                make_documents(fa_list).then(function openPrintWindow(html) {
                    w.document.open();
                    w.document.write(html);
                    w.document.close();
                    $timeout(w.print, 300);
                }, function (error) {
                    w.close();
                    alert(error);
                });
            };

            $scope.reloadClient();
        }
    ]);