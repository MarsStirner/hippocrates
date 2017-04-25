'use strict';

var EventHospModalCtrl = function ($scope, $q, PrintingService, WMConfig,
        CurrentUser, RefBookService, EventType, AccountingService, ContractModalService,
        WMWindowSync, WMEventFormState, WMEventService, wmevent) {
    $scope.event = wmevent;
    $scope.create_mode = !$scope.event.event_id;
    $scope.alerts = [];

    $scope.ps = new PrintingService('event');
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event.event_id
        }
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.rbFinance = RefBookService.get('rbFinance');
    $scope.rbEventType = new EventType();
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.formstate = WMEventFormState;

    $scope.request_type = {};
    $scope.finance = {};
    $scope.available_contracts = {
        list: []
    };
    $scope.available_pricelists = {
        list: []
    };
    $scope.editing = {
        submit_attempt: false
    };

    var only_create_widgets = ['request_type', 'finance', 'contract', 'event_type', 'set_date'];
    $scope.widget_disabled = function (widget_name) {
        if (only_create_widgets.has(widget_name)) {
            return !$scope.create_mode;
        }
    };

    var stat_req_types = ['clinic', 'hospital', 'stationary'];
    $scope.filter_rb_request_type = function() {
        return function(elem) {
            return (stat_req_types.indexOf(elem.code) >= 0) && elem.relevant;
        };
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
        $scope.update_form_state();
        $scope.update_contract();
    };
    $scope.on_set_date_changed = function () {
        $scope.on_event_type_changed();
    };
    $scope.update_form_state = function () {
        $scope.formstate.set_state(
            $scope.event.info.event_type.request_type,
            $scope.event.info.event_type.finance,
            $scope.create_mode
        );
    };
    $scope.isContractListEmpty = function () {
        return $scope.available_contracts.list.length === 0;
    };
    $scope.isContractDraft = function () {
        return !!safe_traverse($scope.event, ['info', 'contract', 'draft']);
    };
    $scope.isContractListEmptyLabelVisible = function () {
        return $scope.create_mode && $scope.isContractListEmpty();
    };
    $scope.isContractDraftLabelVisible = function () {
        return $scope.isContractDraft();
    };
    $scope.createContract = function () {
        var client_id = safe_traverse($scope.event, ['info', 'client', 'info', 'id']),
            finance_id = safe_traverse($scope.event, ['info', 'event_type', 'finance', 'id']),
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
    function set_rt_finance_choices() {
        var et = safe_traverse($scope.event, ['info', 'event_type']);
        $scope.request_type.selected = et ?
            angular.extend({}, et.request_type) :
            $scope.rbRequestType.get_by_code('hospital');
        $scope.finance.selected = et ? angular.extend({}, et.finance) : undefined;
    }
    function refreshAvailableContracts() {
        var client_id = $scope.event.info.client.info.id,
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
                        if (!safe_traverse($scope.event, ['info', 'contract'])) {
                            $scope.event.info.contract = result;
                        }
                    })
                }
            });
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

    $scope.recalcBodyArea = function() {
        var w = safe_traverse($scope.event, ['received', 'weight', 'value']),
            h = safe_traverse($scope.event, ['received', 'height', 'value']);
        if (w && h) {
            $scope.event.received.body_area = Math.sqrt(w * h / 3600).toFixed(2);
        } else {
            $scope.event.received.body_area = null;
        }
    };
    $scope.saveEvent = function (hospForm) {
        var deferred = $q.defer();
        $scope.editing.submit_attempt = true;
        if (hospForm.$valid) {
            WMEventService.save_hosp($scope.event).then(function (result) {
                hospForm.$setPristine();
                $scope.refreshEvent(result.id)
                    .then(function () {
                        deferred.resolve($scope.event);
                    });
            });
        } else {
            deferred.reject();
        }
        return deferred.promise;
    };
    $scope.saveAndClose = function (hospForm) {
        $scope.saveEvent(hospForm).then(function (event) {
            $scope.$close($scope.event);
        });
    };
    $scope.refreshEvent = function (event_id) {
        return WMEventService.refresh_hosp($scope.event, event_id)
            .then(function (hosp_event) {
                $scope.create_mode = false;
                $scope.recalcBodyArea();
            });
    };
    $scope.getEventPrintContext = function () {
        return !$scope.create_mode ? $scope.event.info.event_type.print_context : null;
    };

    $scope.init = function() {
        $scope.event.info.set_date = new Date($scope.event.info.set_date);
        $scope.recalcBodyArea();

        var et_loading = $scope.rbEventType.initialize($scope.event.info.client.info);
        $q.all([et_loading, $scope.rbRequestType.loading, $scope.rbFinance.loading])
            .then(function () {
                if ($scope.create_mode) {
                    $scope.event.info.event_type = $scope.rbEventType.get_available_et(
                        $scope.event.info.event_type);
                }
                set_rt_finance_choices();
                $scope.on_event_type_changed();
            });
    }

    $scope.init();
};


WebMis20.controller('EventHospModalCtrl', ['$scope', '$q', 'PrintingService',
    'WMConfig', 'CurrentUser', 'RefBookService', 'EventType', 'AccountingService',
    'ContractModalService', 'WMWindowSync', 'WMEventFormState', 'WMEventService',
    EventHospModalCtrl]);
