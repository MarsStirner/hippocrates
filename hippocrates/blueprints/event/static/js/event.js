/**
 * Created by mmalkov on 11.07.14.
 */
var EventDiagnosesCtrl = function ($scope) {
    $scope.can_view_diagnoses = function () {
        return $scope.event.access.can_read_diagnoses;
    };
    $scope.can_open_diagnoses = function () {
        return $scope.event.access.can_edit_diagnoses;
    };
};
var EventMainInfoCtrl = function ($scope, $q, RefBookService, EventType, $filter, CurrentUser,
                                  AccountingService, ContractModalService, WMConfig, WMWindowSync, WMEventFormState) {
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.rbFinance = RefBookService.get('rbFinance');
    $scope.rbEventType = new EventType();
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbResult = RefBookService.get('rbResult');
    $scope.rbAcheResult = RefBookService.get('rbAcheResult');
    $scope.formstate = WMEventFormState;

    $scope.request_type = {};
    $scope.finance = {};
    $scope.available_contracts = {
        list: []
    };
    $scope.available_pricelists = {
        list: []
    };
    var event_created = !$scope.event.is_new(),
        main_user = CurrentUser.get_main_user();

    $scope.widget_disabled = function (widget_name) {
        if (['request_type', 'finance', 'contract', 'event_type',
             'exec_person', 'org_structure', 'set_date'
        ].has(widget_name)) {
            return event_created || $scope.event.ro;
        } else if (widget_name === 'exec_person') {
            return event_created || $scope.event.ro || !CurrentUser.current_role_in('admin', 'clinicRegistrator');
        } else if (['result', 'ache_result'].has(widget_name)) {
            return !(CurrentUser.current_role_in('admin') ||
                !$scope.event.ro && (
                    (
                        (($scope.formstate.is_policlinic() || $scope.formstate.is_stationary()) && (
                            main_user.id === safe_traverse($scope.event, ['info', 'exec_person', 'id']) ||
                            main_user.id === safe_traverse($scope.event, ['info', 'create_person_id'])
                        )) || (
                            $scope.formstate.is_diagnostic() && $scope.userHasResponsibilityByAction
                        )
                    ) && (
                        CurrentUser.current_role_in('clinicRegistrator') ?
                            $scope.formstate.is_paid() :
                            true
                    )
                )
            );
        } else if (['exec_date'].has(widget_name)) {
            return $scope.event.ro;
        }
    };
    $scope.services_added = function () {
        return $scope.event.is_new() && $scope.event.services.length;
    };
    $scope.cmb_result_available = function () {
        return !$scope.create_mode;
    };
    $scope.cmb_ache_result_available = function () {
        return !$scope.create_mode && !$scope.formstate.is_diagnostic();
    };
    $scope.isContractListEmpty = function () {
        return $scope.available_contracts.list.length === 0;
    };
    $scope.isContractDraft = function () {
        return !!safe_traverse($scope, ['event', 'info', 'contract', 'draft']);
    };
    $scope.isContractListEmptyLabelVisible = function () {
        return $scope.create_mode && $scope.isContractListEmpty();
    };
    $scope.isContractDraftLabelVisible = function () {
        return $scope.isContractDraft();
    };
    $scope.setEventFormState = function () {
        // Тип обращения - "Круглосуточный стационар"
        return $scope.formstate.set_state(safe_traverse($scope, ['request_type', 'selected', 'code']));
    };

    $scope.createContract = function () {
        var client_id = safe_traverse($scope.event.info, ['client_id']),
            finance_id = safe_traverse($scope.event.info, ['event_type', 'finance', 'id']),
            client = $scope.event.info.client;
        AccountingService.get_contract(undefined, {
            finance_id: finance_id,
            client_id: client_id,
            payer_client_id: client_id,
            generate_number: true
        })
            .then(function (contract) {
                return ContractModalService.openEdit(contract, client);
            })
            .then(function (result) {
                var contract = result.contract;
                refreshAvailableContracts()
                    .then(function () {
                        set_contract(contract.id)
                    });
            });
    };
    $scope.editContract = function (idx) {
        if (!$scope.event.info.contract) return;
        var contract = _.deepCopy($scope.event.info.contract);
        ContractModalService.openEdit(contract)
            .then(function (result) {
                var upd_contract = result.contract;
                refreshAvailableContracts()
                    .then(function () {
                        set_contract(upd_contract.id)
                    });
            });
    };
    $scope.createContractFromDraft = function () {
        if (!safe_traverse($scope, ['event', 'info', 'contract', 'draft'])) return;
        AccountingService.get_contract($scope.event.info.contract.id, {
            undraft: true
        }).then(function (contract) {
            ContractModalService.openEdit(contract)
                .then(function (result) {
                    refreshAvailableContracts()
                        .then(function () {
                            set_contract(result.contract.id)
                        });
                });
        })
        
    };
    $scope.openContractListUi = function () {
        WMWindowSync.openTab(WMConfig.url.accounting.html_contract_list, refreshAvailableContracts);
    };

    $scope.filter_rb_request_type = function(request_type_kind) {
        return function(elem) {
            if (request_type_kind == 'policlinic'){
                return elem.relevant && (elem.code == 'policlinic' || elem.code == '4' || elem.code == 'diagnosis' || elem.code == 'diagnostic');
            } else if (request_type_kind == 'stationary'){
                return elem.relevant && (['clinic', 'hospital', 'stationary'].indexOf(elem.code)>=0);
            } else {
                return elem.relevant
            }

        };
    };
    $scope.filter_results = function(event_purpose) {
        return function(elem) {
            return elem.eventPurpose_id == event_purpose;
        };
    };

    $scope.exec_person_changed = function () {
        $scope.event.info.org_structure = $scope.event.info.exec_person.org_structure;
    };
    $scope.on_request_type_changed = function () {
        $scope.finance.selected = $scope.rbEventType.get_finances_by_rt(
            $scope.request_type.selected.id
        )[0];
        $scope.update_form_state();
        $scope.on_finance_changed();
        $scope.setEventFormState();
    };
    $scope.on_finance_changed = function () {
        $scope.event.info.event_type = $scope.rbEventType.get_filtered_by_rtf(
            $scope.request_type.selected.id,
            $scope.finance.selected.id
        )[0];
        $scope.update_form_state();
        $scope.on_event_type_changed();

        if(['8', 'admperm1', 'admperm2'].indexOf($scope.event.info.event_type.finance.code) !== -1) {
            $scope.set_default_dates();
        }
    };

    $scope.set_default_dates = function () {
        if($scope.event.is_new()) {
            $scope.event.info.set_date = new Date();
            $scope.event.info.set_date.setHours(1, 0, 0);

            $scope.event.info.exec_date = new Date();
            $scope.event.info.exec_date.setHours(23, 59, 59);
        }
    };

    $scope.on_event_type_changed = function () {
        clearErrors();
        $scope.update_form_state();
        $scope.update_policies();
        $scope.update_contract();
    };
    $scope.on_set_date_changed = function () {
        $scope.on_event_type_changed();
    };

    $scope.update_form_state = function () {
        $scope.formstate.set_state(
            $scope.event.info.event_type.request_type,
            $scope.event.info.event_type.finance,
            $scope.event.is_new()
        );
    };
    $scope.update_policies = function () {
        if ($scope.formstate.is_oms() && $scope.create_mode) {
            refreshAvailableOmsPolicy();
        } else if ($scope.formstate.is_dms()) {
            refreshAvailableDmsPolicy();
        }
    };
    $scope.update_contract = function () {
        if ($scope.create_mode) {
            refreshAvailableContracts()
                .then(function () {
                    set_contract();
                });
        }
    };

    function contract_list_has_draft(list) {
        return _.filter(list, function (item) { return item && !!item.draft }).length > 0;
    }
    function clearErrors() {
        for (var key in $scope.formErrors){
            if ($scope.formErrors.hasOwnProperty(key)){
                delete $scope.formErrors[key];
            }
        }
    }
    function setError(field, message) {
        $scope.formErrors[field] = message;
    }
    function set_rt_finance_choices() {
        var et = safe_traverse($scope.event, ['info', 'event_type']);
        $scope.request_type.selected = et ?
            angular.extend({}, et.request_type) :
            $scope.rbRequestType.get_by_code('policlinic');
        $scope.setEventFormState();
        $scope.finance.selected = et ? angular.extend({}, et.finance) : undefined;
    }
    function refreshAvailableContracts() {
        var client_id = $scope.event.info.client_id,
            finance_id = safe_traverse($scope.event, ['info', 'event_type', 'finance', 'id']),
            set_date = aux.format_date($scope.event.info.set_date);
        return AccountingService.get_available_contracts(client_id, finance_id, set_date)
            .then(function (contract_list) {
                $scope.available_contracts.list = contract_list;
                if (!contract_list_has_draft(contract_list)) {
                    AccountingService.get_contract(undefined, {
                        finance_id: finance_id,
                        client_id: client_id,
                        payer_client_id: client_id,
                        draft: 1
                    }).then(function (result) {
                        contract_list.push(result);
                        if (!safe_traverse($scope, ['event', 'info', 'contract'])) {
                            $scope.event.info.contract = result;
                        }
                    })
                }
            });
    }
    function refreshAvailableOmsPolicy() {
        var policy = $scope.event.info.client.compulsory_policy;
        if (!policy) {
            setError('policy_oms', 'У пациента не указан полис ОМС');
            return;
        } else {
            if (!policy.beg_date || moment(policy.beg_date).startOf('d').isAfter($scope.event.info.set_date)) {
                setError('policy_oms', 'Дата начала действия полиса ОМС не установлена или превышает дату создания обращения');
                return;
            }
            if (moment($scope.event.info.set_date).isAfter(moment(policy.end_date).endOf('d'))) {
                setError('policy_oms', 'Дата создания обращения превышает дату окончания действия полиса ОМС');
                return;
            }
        }
        return policy;
    }
    function refreshAvailableDmsPolicy() {
        var policies = $scope.event.info.client.voluntary_policies;
        if (!policies.length) {
            setError('policy_dms', 'У пациента не указан действующий полис ДМС');
            return;
        } else {
            policies = policies.filter(function (policy) {
                return !(!policy.beg_date || moment(policy.beg_date).startOf('d').isAfter($scope.event.info.set_date)) &&
                    !(!policy.end_date || moment($scope.event.info.set_date).isAfter(moment(policy.end_date).endOf('d')));
            });
            if (!policies.length) {
                setError('policy_dms', 'У пациента нет ни одного валидного полиса ДМС');
                return;
            }
        }
        return policies;
    }
    function set_contract(contract_id) {
        if (!contract_id) {
            $scope.event.info.contract = !$scope.isContractListEmpty() ?
                $scope.available_contracts.list[0] :
                null;
        } else {
            var idx = _.findIndex($scope.available_contracts.list, function (con) {
                return con.id === contract_id;
            });
            $scope.event.info.contract = $scope.available_contracts.list[idx];
        }
    }

    $scope.$watch('event.info.set_date', function (n, o) {
        // при выборе не сегодняшнего дня ставить время 08:00
        if (n !== o && moment(n).startOf('d').diff(moment(o).startOf('d'), 'days') !== 0) {
            var nd = moment(n).set({hour: 8, minute: 0, second: 0});
            $scope.event.info.set_date = nd;
        }
    });

    $scope.$watch('event.info.exec_date', function (n, o) {
        if(n !== undefined && typeof n === 'string' && n !== o) {
            var date = new Date(n);
            if(typeof o === 'object') {
                date.setHours(o.getHours(),o.getMinutes(),o.getSeconds())
            }

            $scope.event.info.exec_date = date
        }
    });

    $scope.$on('event_loaded', function() {
        if(['8', 'admperm1', 'admperm2'].indexOf($scope.event.info.event_type.finance.code) !== -1) {
            if(!$scope.event.info.set_date) {
                $scope.event.info.set_date = new Date();
                $scope.event.info.set_date.setHours(1, 0, 0);
            }
            if(!$scope.event.info.exec_date) {
                $scope.event.info.exec_date = new Date();
                $scope.event.info.exec_date.setHours(23, 59, 59);
            }
        } else {
            $scope.event.info.set_date = new Date($scope.event.info.set_date);
        }

        var et_loading = $scope.rbEventType.initialize($scope.event.info.client);
        $q.all([et_loading, $scope.rbRequestType.loading, $scope.rbFinance.loading])
            .then(function () {
                if ($scope.create_mode) {
                    $scope.event.info.event_type = $scope.rbEventType.get_available_et($scope.event.info.event_type);
                }
                set_rt_finance_choices();
                $scope.on_event_type_changed();
            });
        $scope.userHasResponsibilityByAction = $scope.event.info.actions ?
            $scope.event.info.actions.some(function (action) {
                return [action.person_id, action.create_person_id, action.set_person_id].has(main_user.id);
            }) :
            false;
    });
};


var EventReceivedCtrl = function($scope, $modal, RefBookService, WMEventFormState) {
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbHospitalisationGoal = RefBookService.get('rbHospitalisationGoal');
    $scope.rbHospitalisationOrder = RefBookService.get('rbHospitalisationOrder');
    $scope.formstate = WMEventFormState;

    $scope.received_edit = function(){
        var scope = $scope.$new();
        scope.model = angular.copy($scope.event.received);
        $modal.open({
            templateUrl: 'modal-received.html',
            backdrop : 'static',
            windowClass: 'modal-scrollable',
            size: 'lg',
            scope: scope,
            resolve: {
                model: function () {
                    return $scope.event.received;
                }
            }
        }).result.then(function (rslt) {
            $scope.event.received = rslt;
        });
    }

};

var EventMovingsCtrl = function($scope, $modal, RefBookService, ApiCalls, WMConfig, WebMisApi) {
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbHospitalBedProfile = RefBookService.get('rbHospitalBedProfile');

    $scope.refreshMovings = function () {
        return WebMisApi.stationary.get_movings($scope.event.event_id)
            .then(function (movings) {
                Array.prototype.splice.apply(
                    $scope.event.movings,
                    [0, $scope.event.movings.length].concat(movings)
                );
            });
    };
    $scope.moving_save = function (moving){
        return ApiCalls.wrapper('POST', WMConfig.url.event.moving_save, {}, moving)
    };
    $scope.create_moving = function(){
        var scope = $scope.$new();
        scope.model = {
            event_id: $scope.event.event_id,
            beg_date: new Date()
        };
        $modal.open({
            templateUrl: 'modal-create-moving.html',
            backdrop : 'static',
            size: 'lg',
            scope: scope
        }).result.then(function (result) {
            $scope.moving_save(result).then(function (result) {
                $scope.refreshMovings();
            });
        });
    };

    $scope.change_moving = function(){
        var scope = $scope.$new();
        scope.model = {
            event_id: $scope.event.event_id,
            beg_date: new Date()
        };
        $modal.open({
            templateUrl: 'modal-create-moving.html',
            backdrop : 'static',
            size: 'lg',
            scope: scope
        }).result.then(function (result) {
            $scope.close_last_moving().then(function () {
                $scope.moving_save(result).then(function (result) {
                    $scope.refreshMovings();
                });
            });
        });
    };

    $scope.edit_moving = function(moving){
        var scope = $scope.$new();
        scope.model = angular.copy(moving);
        scope.event_admission_date = $scope.event.admission_date;
        $scope.org_struct_changed(scope.model).then(function(){
            $modal.open({
                templateUrl: 'modal-create-hospBed.html',
                backdrop : 'static',
                size: 'lg',
                scope: scope
            }).result.then(function (result) {
                $scope.moving_save(result).then(function (result) {
                    $scope.refreshMovings();
                });
            });
        });
    };

    $scope.close_last_moving = function(){
        var moving = $scope.event.movings.length ? $scope.event.movings[$scope.event.movings.length - 1] : null;
        return ApiCalls.wrapper('POST', WMConfig.url.event.moving_close, {}, moving).then(function(result){
            $scope.refreshMovings();
        })
    };

    $scope.create_hospitalBed = function(moving){
        var scope = $scope.$new();
        scope.model = angular.copy(moving);
        $scope.org_struct_changed(scope.model).then(function(){
            $modal.open({
                templateUrl: 'modal-create-hospBed.html',
                backdrop : 'static',
                size: 'lg',
                scope: scope
            }).result.then(function (result) {
                $scope.moving_save(result).then(function (result) {
                    $scope.refreshMovings();
                });
            });
        })
    };

    $scope.org_struct_changed = function(model){
        var hb_id = model.HospitalBed ? model.HospitalBed.id : null;
        return ApiCalls.wrapper('GET', WMConfig.url.event.hosp_beds, {
            org_str_id : model.orgStructStay.value.id,
            hb_id: hb_id
        }).then(function (result) {
            model.hosp_beds = result;
            model.hospitalBedProfile.value = null;
        })
    };

    $scope.choose_hb = function(moving, hb){
        moving.hosp_beds.map(function(hbed){
            hbed.chosen = false;
        });
        moving.hospitalBed.value = hb;
        moving.hospitalBedProfile.value = hb.profile;
        hb.chosen = true;
    }
};

var EventServicesCtrl = function($scope, $rootScope, $timeout, AccountingService, InvoiceModalService, PrintingService) {
    $scope.query = "";
    $scope.search_result = null;
    $scope.search_processed = false;
    $scope.editing = false;
    $scope.editingInvoice = false;
    $scope.pager = {
        current_page: 1,
        per_page: 10,
        max_pages: 10,
        pages: null,
        record_count: null
    };
    $scope.newInvoiceServiceList = [];
    $scope.newInvoiceServiceMap = {};
    $scope.ps_invoice = new PrintingService("invoice");

    $scope.refreshServiceList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        return AccountingService.get_paginated_services(
            $scope.event.event_id, $scope.pager.current_page, $scope.pager.per_page
        )
            .then(function (paged_data) {
                $scope.event.services = paged_data.service_list;
                $scope.pager.record_count = paged_data.count;
                $scope.pager.pages = paged_data.total_pages;

                $scope.hideLabSubservices();
            });
    };
    $scope.onPageChanged = function () {
        $scope.refreshServiceList(true)
            .then(function () {
                if ($scope.inInvoiceEditMode()) {
                    angular.forEach($scope.event.services, function (service) {
                        service.in_new_invoice = $scope.newInvoiceServiceList.some(function (s) {
                            return s.id === service.id;
                        });
                    });
                }
            });
    };

    $scope.controlsAvailable = function () {
        return $scope.event.access.invoice_all;
    };
    $scope.inEditMode = function () {
        return $scope.editing;
    };
    $scope.startEditing = function () {
        $scope.editing = true;
    };
    $scope.cancelEditing = function () {
        $scope.query_clear();
        $scope.editing = false;
        $scope.refreshServiceList(true);
    };
    $scope.finishEditing = function () {
        AccountingService.save_service_list(
            $scope.event.event_id, $scope.event.services, $scope.pager.current_page, $scope.pager.per_page
        )
            .then(function (paged_data) {
                $scope.event.services = paged_data.service_list;
                $scope.pager.record_count = paged_data.count;
                $scope.pager.pages = paged_data.total_pages;

                $scope.query_clear();
                $scope.editing = false;
                $rootScope.$broadcast('servicesDataChanged');
                $scope.hideLabSubservices();
            });
    };
    $scope.inInvoiceEditMode = function () {
        return $scope.editingInvoice;
    };
    $scope.btnMakeInvoiceDisabled = function () {
        return !$scope.newInvoiceServiceList.length;
    };
    $scope.startEditingInvoice = function () {
        $scope.editingInvoice = true;
        AccountingService.get_services_not_in_invoice($scope.event.event_id)
            .then(function (service_list) {
                var processed = {};
                $scope.newInvoiceServiceMap = _.indexBy(service_list, 'id');
                angular.forEach($scope.event.services, function (service) {
                    if ($scope.newInvoiceServiceMap.hasOwnProperty(service.id)) {
                        service.in_new_invoice = true;
                        $scope.newInvoiceServiceList.push(service);
                        processed[service.id] = service;
                    }
                });
                // services from other pages
                angular.forEach($scope.newInvoiceServiceMap, function (service, service_id) {
                    if (!processed.hasOwnProperty(service_id)) {
                        $scope.newInvoiceServiceList.push(service);
                    }
                });
            });
    };
    $scope.cancelEditingInvoice = function () {
        $scope.editingInvoice = false;
        $scope.newInvoiceServiceList.splice(0, $scope.newInvoiceServiceList.length);
        $scope.newInvoiceServiceMap = {};
    };
    $scope.finishEditingInvoice = function () {
        var contract_id = safe_traverse($scope.event.info, ['contract', 'id']);
        InvoiceModalService.openNew($scope.newInvoiceServiceList, contract_id, $scope.event)
            .then(function (result) {
                $scope.event.invoices.push(result.invoice);
                $scope.cancelEditingInvoice();
                $scope.refreshServiceList(true);
                $rootScope.$broadcast('servicesDataChanged');
            });
    };
    $scope.openInvoice = function (idx) {
        var invoice = $scope.event.invoices[idx];
        InvoiceModalService.openEdit(invoice.id, $scope.event)
            .then(function (result) {
                var status = result.status;
                if (status === 'ok') {
                    $scope.event.invoices.splice(idx, 1, result.invoice);
                    $scope.refreshServiceList(true);
                } else if (status === 'del') {
                    $scope.event.invoices.splice(idx, 1);
                    $scope.refreshServiceList(true);
                }
            });
    };
    $scope.search_disabled = function () {
        return $scope.event.ro || !$scope.inEditMode();
    };

    $scope.perform_search = function (query) {
        $scope.search_processed = false;
        if (!query) {
            $scope.search_result = null;
        } else {
            var contract_id = safe_traverse($scope.event.info, ['contract', 'id']),
                client_id = $scope.event.info.client_id;
            AccountingService.search_mis_action_services(query, client_id, contract_id)
                .then(function (search_result) {
                    $scope.search_result = search_result;
                    $scope.search_processed = true;
                });
        }
    };
    $scope.query_clear = function () {
        $scope.search_result = null;
        $scope.query = '';
    };

    $scope.addNewService = function (search_item) {
        AccountingService.get_service(undefined, {
            service_kind_id: safe_traverse(search_item, ['service_kind', 'id']),
            price_list_item_id: search_item.price_list_item_id,
            event_id: $scope.event.info.id,
            serviced_entity_from_search: search_item
        })
            .then(function (new_service) {
                $scope.event.services.push(new_service);
            });
    };
    $scope.get_ps_resolve = function (invoice) {
        return {
            invoice_id: invoice.id,
            event_id: $scope.event.info.id
        }
    };
    var traverseServices = function (service) {
        service.ui_attrs.expanded = (!service.id || service.service_kind.code !== 'lab_action');
        service.ui_attrs.visible = (!service.id || service.service_kind.code !== 'lab_test');
        angular.forEach(service.subservice_list, traverseServices);
    };
    $scope.hideLabSubservices = function () {
        $timeout(function () {
            angular.forEach($scope.event.services, traverseServices);
        }, 0);
    };

    $scope.$on('event_loaded', function() {
        $scope.query_clear();
        $scope.refreshServiceList();
    });
    $scope.$on('eventFormStateChanged', function() {
        $scope.query_clear();
    });
};

var EventInfoCtrl = function ($scope, WMEvent, $http, RefBookService, $window, $document, $timeout, PrintingService,
        $filter, $modal, WMEventServices, WMEventFormState, MessageBox, WMConfig, PatientActionsModalService, localStorageService) {
    $scope.aux = aux;
    $scope.alerts = [];
    $scope.eventServices = WMEventServices;
    $scope.formstate = WMEventFormState;

    var params = aux.getQueryParams(location.search);
    $scope.event_id = params.event_id;
    $scope.client_id = params.client_id;
    $scope.ticket_id = params.ticket_id;
    $scope.request_type_kind = params.requestType_kind;
//    var event = $scope.event = new WMEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
//    $scope.create_mode = $scope.event.is_new();
    $scope.formErrors = {};
    $scope.editing = {
        submit_attempt: false,
        contract_edited: false
    };

    $scope.initialize = function() {
        $scope.event.reload().
            then(function() {
                $scope.$broadcast('event_loaded');
                $scope.formstate.set_state($scope.event.info.event_type.request_type, $scope.event.info.event_type.finance, $scope.event.is_new());
                if (!$scope.event.is_new()) {
                    $scope.ps.set_context($scope.event.info.event_type.print_context);
                }
                if (window.sessionStorage.getItem('AboutToCreate')) {
                    window.sessionStorage.removeItem('AboutToCreate');
                    notifyTabs();
                }

                $scope.$watch(function () {
                    return [safe_traverse($scope.event, ['info', 'event_type', 'request_type']),
                        safe_traverse($scope.event, ['info', 'event_type', 'finance'])];
                }, function (n, o) {
                    if (n !== o) {
                        var rt = n[0],
                            fin = n[1];
                        $scope.formstate.set_state(rt, fin, $scope.event.is_new());
                        $scope.$broadcast('eventFormStateChanged', {
                            request_type: rt,
                            finance: fin
                        });
                    }
                }, true);
            });
    };
    function notifyTabs() {
        var modalsToUpdate = localStorageService.get('modalClientToUpdate') || {};
        modalsToUpdate[$scope.event.info.client_id] = +new Date();
        localStorageService.set('modalClientToUpdate', modalsToUpdate);
        $timeout(function() {
            var modalsToUpdate = localStorageService.get('modalClientToUpdate') || {};
                for (var property in modalsToUpdate) {
                        if (modalsToUpdate.hasOwnProperty(property)) {
                            var diffInSeconds = Math.abs((+new Date() - modalsToUpdate[property])/1000);
                            if (property == $scope.event.info.client_id || diffInSeconds >= 60) {
                                delete modalsToUpdate[property]
                            }
                        }
                }
               localStorageService.set('modalClientToUpdate', modalsToUpdate);
        }, 5000);
    }

    $scope.save_event = function () {
        $scope.editing.submit_attempt = true;
        if (!_.isEmpty($scope.formErrors)) {
            var elm = $('#mainInfoErrorBlock');
            $document.scrollToElement(elm, 100, 1500);
        } else if ($scope.eventForm.$valid) {
            $scope.event.save()
            .then(function (result) {
                $scope.eventForm.$setPristine();
                if ($scope.event.is_new()) {
                    if (result.error_text) {
                        MessageBox.info('Внимание!', result.error_text).then(function () {
                            $window.open(WMConfig.url.event.html.event_info + '?event_id=' + result.event_id, '_self');
                        });
                    } else {
                        window.sessionStorage.setItem('AboutToCreate', true);
                        $window.open(WMConfig.url.event.html.event_info + '?event_id=' + result.event_id, '_self');
                    }
                } else {
                    if (result.error_text) {
                        MessageBox.info('Внимание!', result.error_text).then(function () {
                            $scope.event.reload().then(function () {
                                $scope.$broadcast('event_loaded');
                            });
                        });
                    } else {
                        $scope.event.reload().then(function () {
                            $scope.$broadcast('event_loaded');
                            notifyTabs();
                        });
                    }
                }
                $scope.editing.contract_edited = false;
            }, function (message) {
                MessageBox.info('Ошибка сохранения', message);
            });
        } else {
            var formelm = $('#eventForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
        }
    };

    $scope.delete_event = function () {
        MessageBox.question(
            'Удаление обращения',
            'Вы уверены, что хотите удалить текущее обращение?'
        ).then(function () {
            $scope.eventServices.delete_event(
                $scope.event
            ).then(function () {
                 notifyTabs();
                if (window.opener) {
                    window.opener.focus();
                    window.close();
                }
            }, function (response) {
                var rr = response.data.meta;
                MessageBox.error('Невозможно удалить обращение', safe_traverse(response, ['data', 'meta', 'name']));
            });
        });
    };

    $scope.close_event = function() {
        $scope.eventServices.check_can_close_event($scope.event)
        .then(function () {
            $scope.eventServices.close_event($scope.event)
            .then(function (response) {
                MessageBox.info('Данные сохранены', response.data.meta.name)
                .then(function () {
                    notifyTabs();
                    $scope.eventForm.$setPristine();
                    $window.location.reload(true);
                });
            }, function () {
                alert('Ошибка закрытия обращения');
            });
        }, function () {
            alert('Ошибка закрытия обращения');
        });
    };

    $scope.cancel_editing = function(){
        if (window.opener){
            window.opener.focus();
            window.close();
        }
    };

    $scope.openPatientActions = function () {
        PatientActionsModalService.open($scope.event.info.client_id);
    };

    $scope.ps = new PrintingService("event");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });


};
var StationaryEventInfoCtrl = function ($scope, $filter, $controller, $modal, $http, $q, RisarApi, ApiCalls, WMStationaryEvent, WMConfig) {
    $controller('EventInfoCtrl', {$scope: $scope});
    var event = $scope.event = new WMStationaryEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.create_mode = $scope.event.is_new();
    var recalcBodyArea = function() {
        var w = safe_traverse($scope.event, ['received', 'weight', 'value']),
            h = safe_traverse($scope.event, ['received', 'height', 'value']);
        if (w && h) {
            $scope.event.info.body_area = Math.sqrt(w * h / 3600).toFixed(2);
        }
    };
    $scope.$on('event_loaded', function () {
        recalcBodyArea();
    });
    $scope.format_admission_date = function (date) {
        return date ? $filter('asDateTime')(date) : '&nbsp;';
    };
    $scope.format_discharge_date = function (date) {
        return date ? $filter('asDateTime')(date) : '&nbsp;';
    };
    $scope.format_hosp_length = function (hosp_length) {
        return angular.isNumber(hosp_length) ? String(hosp_length) : '&nbsp;';
    };
    $scope.format_os = function (os) {
        return os ? (os.name) : '&nbsp;';
    };
    $scope.format_hosp_bed = function (hosp_bed) {
        return hosp_bed ? (hosp_bed.name) : '&nbsp;';
    };
    $scope.format_doctor = function (doctor) {
        return doctor ? (doctor.full_name) : '&nbsp;';
    };
    var IntolerancesCtrl = function ($scope, $modalInstance, models, type) {
        $scope.addModel = function () {
            var model = {
                type: intolerance_map[type],
                date: null,
                name: '',
                power: null,
                note: '',
                deleted: 0
            };
            models.push(model);
        };
        $scope.remove = function (p) {
            p.deleted = 1;
        };
        $scope.restore = function (p) {
            p.deleted = 0;
        };

        if (!models || models.length===0) {
            $scope.addModel();
        }
    };

    var BloodHistoryCtrl = function ($scope, $modalInstance, models) {
        $scope.addModel = function () {
            var model = {
                blood_type: null,
                date: null,
                deleted: 0
            };
            models.push(model);
        };
        $scope.remove = function (p) {
            p.deleted = 1;
        };
        $scope.restore = function (p) {
            p.deleted = 0;
        };
    };

    var intolerance_map = {
        allergies: {
            code: 'allergy',
            name: 'Аллергия'
        },
        intolerances: {
            code: 'medicine',
            name: 'Медикаментозная непереносимость'
        }
    };

    $scope.edit_intolerances = function (field) {
        var models = _.map($scope.event[field], function (source) {
            return angular.extend({}, source);
        });
        open_edit(models, field).result.then(function (models) {
            $q.all(
                _.filter(
                    _.map(models, function (model) {
                        if (model.deleted) {
                            if (model.id) {
                                RisarApi.anamnesis.intolerances.delete(model.id, intolerance_map[field].code)
                            }
                        } else {
                            return RisarApi.anamnesis.intolerances.save($scope.event.info.client_id, model)
                        }
                    }),
                    function (deferred) {
                        return deferred !== undefined
                    }
                )
            ).then(function (results) {
                $scope.event[field] = results;
            });
        })
    };
    var open_edit = function (list, type) {
        var scope = $scope.$new();
        scope.models = list;
        scope.type = type;
        return $modal.open({
            templateUrl: 'modal-intolerances.html',
            controller: IntolerancesCtrl,
            backdrop : 'static',
            scope: scope,
            resolve: {
                models: function () {return list},
                type: function() {return type}
            },
            size: 'lg'
        })
    };
    $scope.edit_blood = function () {
        var models = _.map($scope.event.blood_history, function (source) {
            return angular.extend({}, source);
        });
        open_edit_blood(models).result.then(function (models) {
            $q.all(
                _.filter(
                    _.map(models, function (model) {
                        var data = {
                            client_id: $scope.event.info.client_id,
                            blood_type_info: model
                        };
                        return ApiCalls.wrapper('POST', WMConfig.url.event.blood_history, {}, data)
                    }),
                    function (deferred) {
                        return deferred !== undefined
                    }
                )
            ).then(function (results) {
                $scope.event.blood_history = results;
            });
        })
    };
    var open_edit_blood = function (list) {
        var scope = $scope.$new();
        scope.models = list;
        return $modal.open({
            templateUrl: 'modal-blood-history.html',
            controller: BloodHistoryCtrl,
            backdrop : 'static',
            scope: scope,
            resolve: {
                models: function () {return list}
            },
            size: 'lg'
        })
    };

    $scope.initialize();
};
var PoliclinicEventInfoCtrl = function ($scope, $controller, WMPoliclinicEvent) {
    $controller('EventInfoCtrl', {$scope: $scope});
    var event = $scope.event = new WMPoliclinicEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.create_mode = $scope.event.is_new();
    $scope.initialize();

};
var EventQuotingCtrl = function ($scope, RefBookService) {
    var original_quoting = angular.extend({}, $scope.event.vmp_quoting);
    $scope.rbQuotaType = RefBookService.get('QuotaType');
    $scope.rbPatientModel = RefBookService.get('rbPacientModel');
    $scope.rbTreatment = RefBookService.get('rbTreatment');
    $scope.quotaTypeFormatter = function (selected) {
        return selected ? '{0} - {1}'.format(selected.code, selected.name) : undefined;
    };
    $scope.$watch(function () {
        return safe_traverse($scope.event, ['vmp_quoting', 'coupon']);
    }, function (n, o) {
        if (n !== o) {
            if(!$scope.event.vmp_quoting.mkb){
                $scope.event.vmp_quoting.mkb = $scope.event.vmp_quoting.coupon.mkb;
            }
            if(!$scope.event.vmp_quoting.quota_type){
                $scope.event.vmp_quoting.quota_type = $scope.event.vmp_quoting.coupon.quota_type;
            }
        }
    });
};

WebMis20.controller('EventDiagnosesCtrl', ['$scope', 'RefBookService', '$http', EventDiagnosesCtrl]);
WebMis20.controller('EventMainInfoCtrl', ['$scope', '$q', 'RefBookService', 'EventType', '$filter',
    'CurrentUser', 'AccountingService', 'ContractModalService', 'WMConfig', 'WMWindowSync', 'WMEventFormState',
    EventMainInfoCtrl]);
WebMis20.controller('EventReceivedCtrl', ['$scope', '$modal', 'RefBookService', 'WMEventFormState', EventReceivedCtrl]);
WebMis20.controller('EventMovingsCtrl', ['$scope', '$modal', 'RefBookService', 'ApiCalls', 'WMConfig',
    'WebMisApi', EventMovingsCtrl]);
WebMis20.controller('EventServicesCtrl', ['$scope', '$rootScope', '$timeout', 'AccountingService',
    'InvoiceModalService', 'PrintingService', EventServicesCtrl]);
WebMis20.controller('EventInfoCtrl', ['$scope', 'WMEvent', '$http', 'RefBookService', '$window', '$document', '$timeout', 
    'PrintingService', '$filter', '$modal', 'WMEventServices', 'WMEventFormState', 'MessageBox', 'WMConfig',
    'PatientActionsModalService', 'localStorageService', EventInfoCtrl]);
WebMis20.controller('StationaryEventInfoCtrl', ['$scope', '$filter', '$controller', '$modal', '$http', '$q',
    'RisarApi', 'ApiCalls', 'WMStationaryEvent', 'WMConfig', StationaryEventInfoCtrl]);
WebMis20.controller('PoliclinicEventInfoCtrl', ['$scope', '$controller', 'WMPoliclinicEvent', PoliclinicEventInfoCtrl]);
