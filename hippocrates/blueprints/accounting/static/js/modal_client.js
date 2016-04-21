/**
 * Created by mmalkov on 19.04.16.
 */
'use strict';

/* Вы, наверное, думаете: "какого хера это говно делает здесь, учитыавя, что это почти копипаста из другого модуля?"
 * Спросите Сашу, и он вам ответит, что всплывающие вкладки всех бесят. */

WebMis20
.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/client_edit.html',
'\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Создание клиента</h4>\
</div>\
<div class="modal-body">\
    <ng-form name="clientForm" id="clientForm" role="form" novalidate>\
        <ng-form name="mainInfoForm">\
            <div class="box box-primary">\
                <div class="box-header with-border">\
                    <h3 class="box-title">Основная информация</h3>\
                </div>\
                <div class="box-body">\
                    <div class="row">\
                        <div class="form-group col-md-3" ng-class="{\'has-error\': mainInfoForm.lastname.$invalid && (mainInfoForm.lastname.$dirty || editing.submit_attempt)}">\
                            <label for="lastname" class="control-label">Фамилия <span class="text-danger">*</span></label>\
                            <input type="text" class="form-control" autocomplete="off" placeholder="Фамилия" id="lastname" name="lastname" ng-model="client.info.last_name" ng-required="true"/>\
                        </div>\
                        <div class="form-group col-md-3" ng-class="{\'has-error\': mainInfoForm.firstname.$invalid && (mainInfoForm.firstname.$dirty || editing.submit_attempt)}">\
                            <label for="lastname" class="control-label">Имя <span class="text-danger">*</span></label>\
                            <input type="text" class="form-control" autocomplete="off" placeholder="Имя" id="firstname" name="firstname" ng-model="client.info.first_name" ng-required="true"/>\
                        </div>\
                        <div class="form-group col-md-3">\
                            <label for="patronymic">Отчество</label>\
                            <input type="text" class="form-control" autocomplete="off" placeholder="Отчество" id="patronymic" name="patronymic" ng-model="client.info.patr_name"/>\
                        </div>\
                        <div class="form-group col-md-offset-1 col-md-2" ng-class="{\'has-error\': mainInfoForm.gender.$invalid && (mainInfoForm.gender.$dirty || editing.submit_attempt)}">\
                            <label for="gender" class="control-label">Пол <span class="text-danger">*</span></label>\
                            <select class="form-control" id="gender" name="gender" ng-model="client.info.sex" ng-options="item as item.name for item in rbGender.objects track by item.id" ng-required="true">\
                                <option value="">Не выбрано</option>\
                            </select>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="form-group col-md-3" ng-class="{\'has-error\': mainInfoForm.birthdate.$invalid && (mainInfoForm.birthdate.$dirty || editing.submit_attempt)}">\
                            <label for="birthdate" class="control-label">Дата рождения <span class="text-danger">*</span></label>\
                            <wm-date id="birthdate" name="birthdate" ng-model="client.info.birth_date" ng-required="true" max-date="currentDate"></wm-date>\
                        </div>\
                        <div class="form-group col-md-3" ng-class="{\'has-error\': mainInfoForm.snils.$invalid && mainInfoForm.snils.$dirty}">\
                            <label for="snils" class="control-label">СНИЛС</label>\
                            <input type="text" class="form-control" id="snils" name="snils" ui-mask="999-999-999 99"\
                                ng-model="client.info.snils" placeholder="___-___-___ __"\
                                ng-pattern="/\\d{3}-\\d{3}-\\d{3} \\d\\d/" snils-validator\
                                popover="Введён невалидный СНИЛС" popover-placement="right" popover-trigger="show_popover" />\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="form-group col-md-12">\
                            <label for="notes">Примечания</label>\
                            <textarea class="form-control" id="notes" name="notes" rows="2" autocomplete="off" ng-model="client.info.notes"></textarea>\
                        </div>\
                    </div>\
                </div>\
            </div>\
        </ng-form>\
        <ng-form name="_idDocForm">\
            <div ng-repeat="doc in client.id_docs | flt_not_deleted">\
                <ng-form name="idDocForm">\
                    <div class="box box-primary">\
                        <div class="box-header with-border">\
                            <h3 class="box-title">Документ удостоверяющий личность</h3>\
                            <div class="box-tools pull-right">\
                                <button type="button" class="btn btn-box-tool" title="Редактировать"\
                                    ng-click="edit.activated=true" ng-show="doc.id">\
                                    <span class="glyphicon glyphicon-pencil text-primary"></span>\
                                </button>\
                                <button type="button" class="btn btn-box-tool" title="Удалить"\
                                    ng-click="clientServices.delete_document(client, doc)">\
                                    <span class="text-danger glyphicon glyphicon-trash"></span>\
                                </button>\
                            </div>\
                        </div>\
                        <div class="box-body">\
                            <wm-document id-postfix="c[[$index]]"\
                                group-code="1"\
                                model-document="doc"\
                                edit-mode="doc.id ? edit.activated : true">\
                            </wm-document>\
                            <div ng-if="doc.file_attach">\
                                <h5>Копия документа</h5>\
                                <wm-client-file-attach attach-type="document"\
                                    model-attach="doc.file_attach"\
                                    model-doc="doc"\
                                    on-add="add_new_file(documentInfo, policyInfo)"\
                                    on-open="openFile(cfa_id, idx)">\
                                </wm-client-file-attach>\
                                <button type="button" class="btn-link" ng-click="printFilesAttach([doc.file_attach])" title="Печать копии">\
                                    <span class="glyphicon glyphicon-print"></span>\
                                </button>\
                            </div>\
                        </div>\
                    </div>\
                </ng-form>\
            </div>\
        </ng-form>\
        <ng-form name="addressForm">\
            <h4>Адрес регистрации и проживания</h4>\
            <ng-form name="_regaddress" toc-element="Регистрации">\
                <div ng-repeat="reg_addr in client.reg_addresses | flt_not_deleted">\
                    <div class="box box-primary">\
                        <div class="box-header with-border">\
                            <h3 class="box-title">Адрес регистрации</h3>\
                            <div class="box-tools pull-right">\
                                <button type="button" ng-show="reg_addr.id" class="btn btn-box-tool" title="Редактировать"\
                                    ng-click="edit.activated=true">\
                                    <span class="glyphicon glyphicon-pencil text-primary"></span></button>\
                                <button type="button" class="btn btn-box-tool" title="Удалить"\
                                    ng-click="clientServices.delete_address(client, 0, reg_addr)">\
                                    <span class="glyphicon glyphicon-trash text-danger"></span></button>\
                            </div>\
                        </div>\
                        <div class="box-body">\
                            <ng-form name="regAddressForm">\
                                <wm-kladr-address prefix="reg"\
                                    address-model="reg_addr"\
                                    edit-mode="reg_addr.id ? edit.activated : true">\
                                </wm-kladr-address>\
                            </ng-form>\
                        </div>\
                    </div>\
                </div>\
                <div class="panel">\
                    <button type="button" class="btn btn-lg btn-link btn-block"\
                        ng-click="clientServices.add_new_address(client, 0)">\
                        <i class="ion ion-plus-round fa-fw"></i>Добавить адрес регистрации</button>\
                </div>\
            </ng-form>\
            <ng-form name="_liveaddress" toc-element="Проживания">\
                <div ng-repeat="live_addr in client.live_addresses | flt_not_deleted">\
                    <div class="box box-info">\
                        <div class="box-header with-border">\
                            <h3 class="box-title">Адрес проживания</h3>\
                            <div class="box-tools pull-right">\
                                <button ng-show="live_addr.id" type="button" class="btn btn-box-tool" title="Редактировать"\
                                    ng-click="edit.activated=true">\
                                    <span class="glyphicon glyphicon-pencil text-primary"></span></button>\
                                <button type="button" class="btn btn-box-tool" title="Очистить"\
                                    ng-click="clientServices.delete_address(client, 1, live_addr)">\
                                    <span class="glyphicon glyphicon-trash text-danger"></span></button>\
                            </div>\
                        </div>\
                        <div class="box-body">\
                            <ng-form name="locAddressForm">\
                                <wm-kladr-address prefix="loc"\
                                    address-model="live_addr"\
                                    edit-mode="(live_addr.synced ? live_addr.live_id : live_addr.id) ? edit.activated : true">\
                                    <div class="checkbox">\
                                        <label>\
                                            <input type="checkbox" id="[[prefix]]_copy_addr" name="copy_addr"\
                                                ng-model="live_addr.synced"\
                                                ng-change="clientServices.sync_addresses(client, live_addr, live_addr.synced)"\
                                                ng-disabled="(live_addr.synced ? live_addr.live_id : live_addr.id) ? !edit.activated : false"/>\
                                            Совпадает с адресом регистрации\
                                        </label>\
                                    </div>\
                                </wm-kladr-address>\
                            </ng-form>\
                        </div>\
                    </div>\
                </div>\
                <div class="panel">\
                    <button type="button" class="btn btn-lg btn-link btn-block"\
                        ng-click="clientServices.add_new_address(client, 1)">\
                        <i class="ion ion-plus-round fa-fw"></i>Добавить адрес проживания</button>\
                </div>\
            </ng-form>\
        </ng-form>\
    </ng-form>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отменить</button>\
    <button type="button" class="btn btn-primary" ng-disabled="clientForm.$invalid" ng-click="saveAndClose()">Сохранить</button>\
</div>\
'
    )
}])
.service('AccountingClientModal', [
    'ApiCalls', '$modal', '$http', 'WMClient', 'WMClientServices', 'PrintingService', 'RefBookService', '$window',
    '$document', 'FileEditModal', 'WMConfig', '$q', '$timeout',
function (
    ApiCalls, $modal, $http, WMClient, WMClientServices, PrintingService, RefBookService, $window, $document,
    FileEditModal, WMConfig, $q, $timeout) {

    var AccountingClientModalCtrl = function ($scope, $modalInstance) {
        $scope.records = [];
        $scope.aux = aux;
        $scope.rbGender = RefBookService.get('Gender');
        $scope.alerts = [];
        $scope.clientServices = WMClientServices;
        $scope.currentDate = new Date();
        $scope.selected_files = [];

        $scope.client_id = 'new';
        var client = $scope.client = new WMClient($scope.client_id);

        $scope.editing = {
            submit_attempt: false
        };

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

        $scope.saveAndClose = function() {
            var form = this.clientForm;  // Почему this, а не $scope, как в оригинале? Хер знает! Так работает.
            $scope.editing.submit_attempt = true;
            if (form.$invalid) {
                var formelm = $('#clientForm').find('.ng-invalid:not(ng-form):first');
                $document.scrollToElement(formelm, 100, 1500);
                return false;
            }
            $scope.client.info.dirty = true;  // Really dirty hack lol
            $scope.client.save().then(function(new_client_id) {
                $modalInstance.close(new_client_id);
            });
        };

        $scope.refresh_form = function() {
            // this.mainInfoForm.$setPristine(true);  // хер вам
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
                    promises = [];
                angular.forEach(fa_list, function (fa) {
                    angular.forEach(fa.file_document.files, function (fileMeta) {
                        var promise;
                        pages.push(new Image());
                        var idx = pages.length - 1;
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
                });

                $q.all(promises).then(function composeDocument() {
                    var html_pages = '';
                    angular.forEach(pages, function (elem) {
                        html_pages += '<div style="page-break-after: auto">{0}</div>'.format(elem.outerHTML)
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
    };
    this.open = function () {
        var instance = $modal.open({
            templateUrl: '/WebMis20/modal/accounting/client_edit.html',
            controller: AccountingClientModalCtrl,
            backdrop: 'static',
            size: 'lg',
            windowClass: 'modal-scrollable'
        });
        return instance.result.then();
    }
}])
;