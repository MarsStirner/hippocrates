/**
 * Created by mmalkov on 11.07.14.
 */
var EventDiagnosesCtrl = function ($scope) {
    $scope.can_view_diagnoses = function () {
        return $scope.event.can_read_diagnoses;
    };
    $scope.can_open_diagnoses = function () {
        return $scope.event.can_edit_diagnoses;
    };
};
var EventMainInfoCtrl = function ($scope, $q, RefBookService, EventType, $filter, CurrentUser,
                                  AccountingService, ContractModalService, WMConfig, WMWindowSync) {
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.rbFinance = RefBookService.get('rbFinance');
    $scope.rbEventType = new EventType();
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbResult = RefBookService.get('rbResult');
    $scope.rbAcheResult = RefBookService.get('rbAcheResult');

    $scope.request_type = {};
    $scope.finance = {};
    $scope.available_contracts = {
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
        // TODO:
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
    $scope.isContractListEmptyLabelVisible = function () {
        return $scope.create_mode && $scope.isContractListEmpty();
    };

    $scope.createContract = function () {
        var client_id = safe_traverse($scope.event.info, ['client_id']),
            finance_id = safe_traverse($scope.event.info, ['event_type', 'finance', 'id']),
            client = $scope.event.info.client;
        AccountingService.get_contract(undefined, {
            finance_id: finance_id,
            client_id: client_id,
            payer_client_id: client_id
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
    $scope.openContractListUi = function () {
        WMWindowSync.openTab(WMConfig.url.html_contract_list, refreshAvailableContracts);
    };

    $scope.filter_rb_request_type = function(request_type_kind) {
        // TODO:
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
    };
    $scope.on_finance_changed = function () {
        $scope.event.info.event_type = $scope.rbEventType.get_filtered_by_rtf(
            $scope.request_type.selected.id,
            $scope.finance.selected.id
        )[0];
        $scope.update_form_state();
        $scope.on_event_type_changed();
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
        $scope.finance.selected = et ? angular.extend({}, et.finance) : undefined;
    }
    function refreshAvailableContracts() {
        var client_id = $scope.event.info.client_id,
            finance_id = safe_traverse($scope.event, ['info', 'event_type', 'finance', 'id']),
            set_date = aux.format_date($scope.event.info.set_date);
        return AccountingService.get_available_contracts(client_id, finance_id, set_date)
            .then(function (contract_list) {
                $scope.available_contracts.list = contract_list;
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

    $scope.$on('event_loaded', function() {
        $scope.event.info.set_date = new Date($scope.event.info.set_date);
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

var EventStationaryInfoCtrl = function($scope, $filter, $modal, $q, RisarApi, ApiCalls) {
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
                                RisarApi.anamnesis.intolerances.delete(model.id, field)
                            }
                        } else {
                            return RisarApi.anamnesis.intolerances.save($scope.$parent.event.info.client_id, model)
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
                        var data = {client_id: $scope.$parent.event.info.client_id,
                                    blood_type_info: model}
                        return ApiCalls.wrapper('POST', url_blood_history_save, {}, data)
                    }),
                    function (deferred) {
                        return deferred !== undefined
                    }
                )
            ).then(function (results) {
                $scope.event.blood_history = results;
            });
        })
    }
    var open_edit_blood = function (list) {
        var scope = $scope.$new();
        scope.models = list;
        return $modal.open({
            templateUrl: 'modal-blood-history.html',
            controller: BloodHistoryCtrl,
            scope: scope,
            resolve: {
                models: function () {return list}
            },
            size: 'lg'
        })
    };
};

var EventReceivedCtrl = function($scope, $modal, RefBookService) {
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbHospitalisationGoal = RefBookService.get('rbHospitalisationGoal');
    $scope.rbHospitalisationOrder = RefBookService.get('rbHospitalisationOrder');

    $scope.received_edit = function(){
        var scope = $scope.$new();
        scope.model = angular.copy($scope.event.received)
        $modal.open({
            templateUrl: 'modal-received.html',
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

var EventMovingsCtrl = function($scope, $modal, RefBookService, ApiCalls) {
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbHospitalBedProfile = RefBookService.get('rbHospitalBedProfile');

    $scope.moving_save = function (moving){
        return ApiCalls.wrapper('POST', url_moving_save, {}, moving)
    }
    $scope.create_moving = function(){
        var scope = $scope.$new();
        scope.model = {
            event_id: $scope.event.event_id,
            beg_date: new Date()
        };
        $modal.open({
            templateUrl: 'modal-create-moving.html',
            size: 'lg',
            scope: scope
        }).result.then(function (result) {
            $scope.moving_save(result).then(function (result) {
                $scope.event.movings[$scope.event.movings.length - 1] = result[0];
                $scope.event.movings.push(result[1]);
            });
        });
    }

    $scope.close_last_moving = function(){
        var moving = $scope.event.movings.length ? $scope.event.movings[$scope.event.movings.length - 1] : null
        ApiCalls.wrapper('POST', url_moving_close, {}, moving).then(function(result){
            $scope.event.movings[$scope.event.movings.length - 1] = result;
        })
    }

    $scope.create_hospitalBed = function(moving){
        var scope = $scope.$new();
        scope.model = angular.copy(moving);
        $scope.org_struct_changed(scope.model).then(function(){
            $modal.open({
                templateUrl: 'modal-create-hospBed.html',
                size: 'lg',
                scope: scope
            }).result.then(function (result) {
                $scope.moving_save(result).then(function (result) {
                angular.extend(moving, result);
                });
            });
        })
    }

    $scope.org_struct_changed = function(model){
        var hb_id = model.HospitalBed ? model.HospitalBed.id : null;
        return ApiCalls.wrapper('GET', url_hosp_beds_get, {org_str_id : model.orgStructStay.value.id,
                                                           hb_id: hb_id})
            .then(function (result) {
                model.hosp_beds = result;
                model.hospitalBedProfile.value = null;
            })
    }

    $scope.choose_hb = function(moving, hb){
        moving.hosp_beds.map(function(hbed){
            hbed.chosen = false;
        })
        moving.hospitalBed.value = hb;
        moving.hospitalBedProfile.value = hb.profile;
        hb.chosen = true;
    }
};

var EventServicesCtrl = function($scope, $rootScope, AccountingService, InvoiceModalService, PrintingService) {
    $scope.query = "";
    $scope.search_result = null;
    $scope.search_processed = false;
    $scope.editing = false;
    $scope.editingInvoice = false;
    $scope.newInvoiceServiceList = [];
    $scope.ps_invoice = new PrintingService("invoice");

    $scope.controlsAvailable = function () {
        return !$scope.event.ro;
    };
    $scope.inEditMode = function () {
        return $scope.editing;
    };
    $scope.startEditing = function () {
        $scope.oldServices = _.deepCopy($scope.event.services);
        $scope.editing = true;
    };
    $scope.cancelEditing = function () {
        $scope.query_clear();
        $scope.editing = false;
        $scope.event.services = $scope.oldServices;
    };
    $scope.finishEditing = function () {
        AccountingService.save_service_list($scope.event.event_id, $scope.event.services.grouped)
            .then(function (service_data) {
                $scope.event.services = service_data;
                $scope.query_clear();
                $scope.editing = false;
                $rootScope.$broadcast('serviceListChanged');
            });
    };
    $scope.inInvoiceEditMode = function () {
        return $scope.editingInvoice;
    };
    $scope.startEditingInvoice = function () {
        $scope.editingInvoice = true;
    };
    $scope.cancelEditingInvoice = function () {
        $scope.newInvoiceServiceList.splice(0, $scope.newInvoiceServiceList.length);
        $scope.editingInvoice = false;
    };
    $scope.finishEditingInvoice = function () {
        var contract_id = safe_traverse($scope.event.info, ['contract', 'id']);
        InvoiceModalService.openNew($scope.newInvoiceServiceList, contract_id, $scope.event)
            .then(function (result) {
                $scope.event.invoices.push(result.invoice);
                $scope.cancelEditingInvoice();
                AccountingService.get_listed_services($scope.event.event_id)
                    .then(function (service_data) {
                        $scope.event.services = service_data;
                    });
            });
    };
    $scope.openInvoice = function (idx) {
        var invoice = _.deepCopy($scope.event.invoices[idx]);
        InvoiceModalService.openEdit(invoice, $scope.event)
            .then(function (result) {
                var status = result.status;
                if (status === 'ok') {
                    $scope.event.invoices.splice(idx, 1, result.invoice);
                } else if (status === 'del') {
                    $scope.event.invoices.splice(idx, 1);
                    // TODO: refresh service list?
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
            // on top level this can be ActionType.id for simple and lab services
            // or undefined for service groups
            serviced_entity_id: safe_traverse(search_item, ['serviced_entity', 'at_id'])
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

    $scope.get_class = function (service) {
        var result = [];
        result.push('info');
        return result;
    };

    $scope.$on('event_loaded', function() {
        $scope.query_clear();
    });
    $scope.$on('eventFormStateChanged', function() {
        $scope.query_clear();
    });
};

var EventInfoCtrl = function ($scope, WMEvent, $http, RefBookService, $window, $document, PrintingService,
        $filter, $modal, WMEventServices, WMEventFormState, MessageBox) {
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
                            $window.open(url_for_event_html_event_info + '?event_id=' + result.event_id, '_self');
                        });
                    } else {
                        $window.open(url_for_event_html_event_info + '?event_id=' + result.event_id, '_self');
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
var StationaryEventInfoCtrl = function ($scope, $controller, $modal, $http, WMStationaryEvent) {
    $controller('EventInfoCtrl', {$scope: $scope});
    var event = $scope.event = new WMStationaryEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.create_mode = $scope.event.is_new();
    $scope.initialize();
};
var PoliclinicEventInfoCtrl = function ($scope, $controller, WMPoliclinicEvent) {
    $controller('EventInfoCtrl', {$scope: $scope});
    var event = $scope.event = new WMPoliclinicEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.create_mode = $scope.event.is_new();
    $scope.initialize();

};


WebMis20.controller('EventDiagnosesCtrl', ['$scope', 'RefBookService', '$http', EventDiagnosesCtrl]);
WebMis20.controller('EventMainInfoCtrl', ['$scope', '$q', 'RefBookService', 'EventType', '$filter',
    'CurrentUser', 'AccountingService', 'ContractModalService', 'WMConfig', 'WMWindowSync', EventMainInfoCtrl]);
WebMis20.controller('EventStationaryInfoCtrl', ['$scope', '$filter', '$modal', '$q', 'RisarApi', 'ApiCalls', EventStationaryInfoCtrl]);
WebMis20.controller('EventReceivedCtrl', ['$scope', '$modal', 'RefBookService', EventReceivedCtrl]);
WebMis20.controller('EventMovingsCtrl', ['$scope', '$modal', 'RefBookService', 'ApiCalls', EventMovingsCtrl]);
WebMis20.controller('EventServicesCtrl', ['$scope', '$rootScope', 'AccountingService',
    'InvoiceModalService', 'PrintingService', EventServicesCtrl]);
WebMis20.controller('EventInfoCtrl', ['$scope', 'WMEvent', '$http', 'RefBookService', '$window', '$document',
    'PrintingService', '$filter', '$modal', 'WMEventServices', 'WMEventFormState', 'MessageBox', EventInfoCtrl]);
WebMis20.controller('StationaryEventInfoCtrl', ['$scope', '$controller', '$modal', '$http', 'WMStationaryEvent', StationaryEventInfoCtrl]);
WebMis20.controller('PoliclinicEventInfoCtrl', ['$scope', '$controller', 'WMPoliclinicEvent', PoliclinicEventInfoCtrl]);
