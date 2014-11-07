/**
 * Created by mmalkov on 11.07.14.
 */
var EventDiagnosesCtrl = function($scope, RefBookService, $http) {
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.rbDiseaseCharacter = RefBookService.get('rbDiseaseCharacter');
    $scope.rbDiseasePhases = RefBookService.get('rbDiseasePhases');
    $scope.rbDiseaseStage = RefBookService.get('rbDiseaseStage');
    $scope.rbHealthGroup = RefBookService.get('rbHealthGroup');
    $scope.rbDispanser = RefBookService.get('rbDispanser');
    $scope.rbTraumaType = RefBookService.get('rbTraumaType');
    $scope.Person = RefBookService.get('Person');

    $scope.$on('event_loaded', function() {
        $scope.diagnoses = $scope.event.diagnoses || [];
    });

    $scope.diag_edit = [];
    $scope.diag_edit_start = function (index) {
        if (!$scope.diag_edit[index]) {
            $scope.diag_edit[index] = angular.extend({}, $scope.diagnoses[index])
        }
    };
    $scope.diag_edit_save = function (index) {
        if ($scope.diag_edit[index]) {
            $scope.diagnoses[index] = $scope.diag_edit[index];
            $scope.diagnoses[index]._dirty = true;
            $scope.diagnoses[index].client_id = $scope.event.info.client_id;
            $scope.diagnoses[index].event_id = $scope.event.info.id;
            $http.post(url_for_event_api_diagnosis_save, $scope.diagnoses[index]).then(function () {
                $scope.diag_edit[index] = undefined;
                delete $scope.diagnoses[index]._first;
            });
        }
    };
    $scope.diag_edit_stop = function (index) {
        if ($scope.diag_edit[index]) {
            if ($scope.diag_edit[index]._first) {
                $scope.diagnoses.splice(index, 1);
            }
            $scope.diag_edit[index] = undefined;
        }
    };
    $scope.diag_edit_new = function () {
        $scope.diagnoses.splice(0, 0, {
            person: $scope.Person.get(current_user_id),
            _new: true,
            _first: true
        });
        $scope.diag_edit_start(0);
    };
    $scope.diag_edit_save_disabled = function (index) {
        var q = $scope.diag_edit[index];
        return !q.diagnosis_type;
    };

};
var EventMainInfoCtrl = function ($scope, $http, RefBookService, EventType, $window, $timeout, Settings, $modal, $filter) {
    $scope.Organisation = RefBookService.get('Organisation');
    $scope.Person = RefBookService.get('vrbPersonWithSpeciality');
    $scope.Contract = RefBookService.get('Contract');
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.rbFinance = RefBookService.get('rbFinance');
    $scope.rbEventType = new EventType();
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbDocumentType = RefBookService.get('rbDocumentType');
    $scope.rbOrder = RefBookService.get('EventOrder');
    $scope.rbPrimary = RefBookService.get('EventPrimary');
    $scope.rbResult = RefBookService.get('rbResult');
    $scope.rbAcheResult = RefBookService.get('rbAcheResult');

    var event_created = !$scope.event.is_new();
    $scope.formcnf = {
        request_type: {
            disabled: event_created
        },
        finance: {
            disabled: event_created
        },
        contract: {
            disabled: event_created
        },
        event_type: {
            disabled: event_created
        },
        exec_person: {
            disabled: event_created || !current_user.current_role_maybe('admin', 'rRegistartor', 'clinicRegistrator')
        },
        org_structure: {
            disabled: event_created
        },
        primacy: {
            disabled: event_created
        },
        order: {
            disabled: event_created
        },
        set_date: {
            disabled: event_created
        },
        exec_date: {
            disabled: $scope.event.closed()
        },
        result: {
            disabled: $scope.event.closed(),
            show: current_user.current_role_maybe('admin', 'doctor')
        },
        ache_result: {
            disabled: !$scope.event.closed(),
            show: current_user.current_role_maybe('admin', 'doctor')
        }
    };

    $scope.finance_is_oms = function(){return $scope._finance.code == '2'};
    $scope.finance_is_dms = function(){return $scope._finance.code == '3'};

    $scope.request_type = {};
    $scope.finance = {};
    $scope.dms = {};
    $scope.contracts = [];
    $scope.policy_errors = [];

    $scope.filter_rb_request_type = function() {
        return function(elem) {
            return elem.code == 'policlinic' || elem.code == '4' ;
        };
    };

    $scope.$on('event_loaded', function() {
        $scope.event.info.set_date = new Date($scope.event.info.set_date);

        $scope.request_type_init = angular.extend({}, $scope.event.info.event_type.request_type);
        $scope.finance_init = angular.extend({}, $scope.event.info.event_type.finance);
        $scope.event_type_init = angular.extend({}, $scope.event.info.event_type);

        $scope.request_type.selected = $scope.request_type_init;
        $scope.finance.selected = $scope.finance_init;
        $scope.$on('rb_load_success_Contract', function (){
            $scope.contracts = $filter('contract_filter')($scope.Contract.objects, $scope.event.info);
        });
    });
    $scope.$watch('request_type.selected', function(new_val, old_val) {
        if (new_val) {
            $scope.finance.selected = $scope.finance_init || $scope.rbEventType.get_finances_by_rt(new_val.id)[0];
            $scope.finance_init = undefined;
        }
    });

    $scope.$watch('finance.selected', function(new_val, old_val) {
        if (new_val) {
            $scope.event.info.event_type = $scope.event_type_init || $scope.rbEventType.get_filtered_by_rtf($scope.request_type.selected.id, new_val.id)[0];
            $scope.event_type_init = undefined;
        }
    });

    $scope.$watch('dms.selected', function(new_val, old_val) {
        if (new_val && new_val != old_val) {
            if (!$scope.check_dms_contract_dependency(new_val, $scope.event.info.contract)) {
                $scope.event.info.contract = undefined;
                var _break = false;
                angular.forEach($scope.contracts, function (contract, key) {
                    if (!_break && $scope.check_dms_contract_dependency(new_val, contract)) {
                        $scope.event.info.contract = contract;
                        _break = true;
                    }
                });
            }
            if (!$scope.check_dms(new_val)){
                $scope.show_policy_errors();
            }else if (!$scope.event.info.contract){
                $scope.add_policy_error('Не заведено договора, соответствующего выбранному полису ДМС');
                $scope.show_policy_errors();
            }
        }
    });

    $scope.$watch('event.info.event_type', function(new_val, old_val) {
        if (new_val != old_val) {
            $scope.contracts = $filter('contract_filter')($scope.Contract.objects, $scope.event.info);
        }
    });

    $scope.$on('form_state_change', function(event, arg) {
        $scope._finance = arg['finance'];
        $scope._contract = arg['contract'];
        $scope.process_policies($scope._finance, $scope._contract);
        // $scope.contracts = $filter('contract_filter')($scope.Contract.objects, $scope.event.info);#}
    });

    $scope.process_policies = function (_finance, _contract) {
        if(!$scope.check_policy()) {
            $scope.show_policy_errors();
            $scope.finance.selected = $scope.rbFinance.get_by_code(4);
        } else {
            if($scope.finance_is_dms() && _contract){
                var _break = false;
                $scope.dms.selected = undefined;
                angular.forEach($scope.event.info.client.voluntary_policies, function (policy, key) {
                    if (!_break && $scope.check_dms_contract_dependency(policy, _contract)){
                        $scope.dms.selected = policy;
                        _break = true;
                    }
                });
                if (!$scope.dms.selected){
                    $scope.add_policy_error('У пациента нет полиса ДМС, связанного с выбранным договором');
                    $scope.show_policy_errors();
                }
            }
        }
    };

    $scope.check_policy = function (){
        if ($scope.finance_is_oms()){
            return $scope.check_oms();
        } else if($scope.finance_is_dms()){
            return $scope.check_dms();
        }
        return true;
    };

    $scope.check_oms = function() {
        var policy = $scope.event.info.client.compulsory_policy;
        if (!policy){
            $scope.add_policy_error('У пациента не указан полис ОМС');
        } else {
            if (!policy.beg_date || moment(policy.beg_date).isAfter($scope.event.info.set_date)) {
                $scope.add_policy_error('Дата начала действия полиса не установлена или превышает дату создания обращения');
            }
            if (moment($scope.event.info.set_date).isAfter(policy.end_date)) {
                $scope.add_policy_error('Дата создания обращения превышает дату окончания действия полиса');
            }
        }
        return $scope.no_policy_errors();
    };

    $scope.check_dms = function (policy) {
        if (policy != undefined){
            if (!policy.beg_date || moment(policy.beg_date).isAfter($scope.event.info.set_date)) {
                // $scope.add_policy_error('Дата начала действия полиса не установлена или превышает дату создания обращения');#}
                return false;
            }
            if (!policy.end_date || moment($scope.event.info.set_date).isAfter(policy.end_date)) {
                // $scope.add_policy_error('Не установлена дата окончания действия полиса или дата создания обращения превышает её');#}
                return false;
            }
        } else {
            var policies = $scope.event.info.client.voluntary_policies;
            if (policies.length == 0){
                $scope.add_policy_error('У пациента не указан действующий полис ДМС');
            } else{
                var has_valid_dms = false;
                angular.forEach(policies, function (value) {
                    if (!has_valid_dms && $scope.check_dms(value)){
                        $scope.clear_policy_errors();
                        has_valid_dms = true;
                    }
                });
                if (!has_valid_dms){
                    $scope.add_policy_error('У пациента нет ни одного валидного полиса ДМС');
                    $scope.dms.selected = undefined;
                }
            }
        }
        return $scope.no_policy_errors();
    };

    $scope.check_dms_contract_dependency = function(_policy, _contract){
        return _policy.insurer.id == _contract.payer.id;
    };

    $scope.exec_person_changed = function () {
        $scope.event.info.org_structure = $scope.event.info.exec_person.org_structure;
    };

    $scope.clear_policy_errors = function () {
        $scope.policy_errors = [];
    };

    $scope.add_policy_error = function (msg) {
        if ($scope.policy_errors.indexOf(msg) == -1) {
            $scope.policy_errors.push(msg);
        }
    };

    $scope.no_policy_errors = function () {
        return $scope.policy_errors.length == 0;
    };

    $scope.show_policy_errors = function () {
        $scope.modal_policy_error($scope.policy_errors);
        $scope.clear_policy_errors();
    };

    $scope.modal_policy_error = function(policy_errors) {
        var modalInstance = $modal.open({
            templateUrl: 'modal-policy-invalid.html',
            resolve: {
                policy_errors: function(){
                    return policy_errors;
                },
                policy_type: function () {
                    return $scope.finance.selected.name;
                }
            },
            controller: PolicyInvalidModalCtrl
        });
    };
};
var PolicyInvalidModalCtrl = function ($scope, $modalInstance, policy_errors, policy_type) {
    $scope.policy_errors = policy_errors;
    $scope.policy_type = policy_type;
    $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
    };
};
var EventPaymentCtrl = function($scope, RefBookService, Settings, $http, $modal) {
    $scope.rbDocumentType = RefBookService.get('rbDocumentType');
    $scope.Organisation = RefBookService.get('Organisation');

    var event_created = !$scope.event.is_new();
    function isNotEmpty(val) { return val !== undefined && val !== null; }

    $scope.payer_is_person = function() {
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return (lc !== null &&
            [lc.first_name, lc.last_name, lc.patr_name, lc.birth_date, lc.doc_type,
                lc.serial_left, lc.serial_right, lc.number, lc.reg_address].some(isNotEmpty)
            );
    };
    $scope.payer_is_org = function() {
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return lc !== null && lc.payer_org;
    };
    $scope.integration1CODVD_enabled = function() {
        return $scope.Settings.get_string('Event.Payment.1CODVD') == '1';
    };
    $scope.contract_info_required = function () {
        return ($scope.formstate.is_paid() || $scope.formstate.is_oms() || $scope.formstate.is_dms()) &&
            !$scope.integration1CODVD_enabled();
    };
    $scope.payer_person_required = function () {
        return ($scope.payer_tabs.person.active && $scope.formstate.is_paid() && $scope.event.info.client.info.age_tuple[3] < 18);
    };
    $scope.payer_org_required = function () {
        return ($scope.payer_tabs.org.active && $scope.formstate.is_paid() && $scope.event.info.client.info.age_tuple[3] < 18);
    };
    $scope.payer_info_disabled = function () {
        return event_created && false;
    };
    $scope.contract_info_disabled = function () {
        return event_created || $scope.integration1CODVD_enabled();
    };
    $scope.btn_edit_contract_info_visible = function () {
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return !(lc && lc.date_contract && lc.number_contract || $scope.integration1CODVD_enabled());
    };
    $scope.import_payer_btn_disabled = function () {
        return event_created && $scope.contract_available();
    };
    $scope.payer_tabs = {
        person: {
            active: true,
            disabled: false
        },
        org: {
            active: false,
            disabled: false
        }
    };

    $scope.refresh_tabs = function (org_active) {
        $scope.payer_tabs.person.active = !org_active;
        $scope.payer_tabs.org.active = Boolean(org_active);
//        $scope.payer_tabs.person.disabled = event_created && $scope.payer_tabs.org.active;
//        $scope.payer_tabs.org.disabled = event_created && $scope.payer_tabs.person.active;
    };

    $scope.contract_available = function () {
        var event = $scope.event;
        return event.payment && event.payment.local_contract && event.payment.local_contract.id;
    };

    $scope.contract_is_shared = function () {
        return $scope.contract_available() && $scope.event.payment.local_contract.shared_in_events.length;
    };

    $scope.get_shared_contract_warning = function () {
        return "Этот договор также используется в других обращениях.Редактирование данных плательщика приведет к созданию нового договора.";
    };

    $scope.payment_box_visible = function () {
        return current_user.current_role_maybe('admin');
    };

    $scope.$on('event_loaded', function() {
        $scope.refresh_tabs($scope.payer_is_org());
    });

    $scope.switch_tab = function(from_tab) {
        if ($scope.switch_in_process) {
            $scope.switch_in_process = false;
            return;
        }
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        if (lc &&
            (
                (from_tab === 0 && $scope.payer_is_person()) ||
                (from_tab === 1 && $scope.payer_is_org())
                )
            ) {
            var modalInstance = $modal.open({
                templateUrl: 'modal-switch-payer.html',
                controller: SwitchPayerModalCtrl,
                resolve: {
                    from_tab: function () {
                        return from_tab;
                    }
                }
            });

            modalInstance.result.then(function () {
                $scope.eventServices.clear_local_contract($scope.event);
            }, function () {
                if (from_tab === 0) {
                    $scope.switch_in_process = true;
                    $scope.payer_tabs.person.active = true;
                } else {
                    $scope.switch_in_process = true;
                    $scope.payer_tabs.org.active = true;
                }
            });
        }
    };

    $scope.clear_payer_lc = function () {
        if (confirm('Данные плательщика будут удалены. Продолжить?')) {
            $scope.eventServices.clear_local_contract($scope.event);
        }
    };

    $scope.get_payer = function(client_id) {
        $http.get(url_api_client_payment_info_get, {
            params: {
                client_id: client_id
            }
        }).success(function(data) {
            $scope.eventServices.update_payment($scope.event, data.result);
            $scope.refresh_tabs($scope.payer_is_org());
        }).error(function() {
            alert('Ошибка получения данных плательщика');
        });
    };

    $scope.open_relatives_modal = function() {
        var modalInstance = $modal.open({
            templateUrl: 'modal-relatives.html',
            controller: RelativesModalCtrl,
            scope: $scope
        });

        modalInstance.result.then(function (selected_client_id) {
            if (selected_client_id) {
                $scope.get_payer(selected_client_id);
            }
        });
    };

    $scope.open_prev_event_contract_modal = function() {
        $scope.eventServices.get_prev_events_contracts(
            $scope.event.info.client_id,
            $scope.event.info.event_type.finance.id,
            $scope.event.info.set_date.toISOString()
        ).then(function (prev_con_info) {
            $modal.open({
                templateUrl: 'modal-prev-event-contract.html',
                size: 'lg',
                controller: PrevEventContractModalCtrl,
                scope: $scope,
                resolve: {
                    model: function () {
                        return prev_con_info;
                    }
                }
            }).result.then(function (selected_lcon) {
                $scope.eventServices.update_payment(
                    $scope.event,
                    {
                        payments: [],
                        local_contract: selected_lcon
                    });
                $scope.refresh_tabs($scope.payer_is_org());
            });
        }, function (message) {
            alert(message);
        });
    };

    $scope.payment_sum = null;
    $scope.process_payment = function () {
        $http.post(
            url_for_event_api_service_make_payment, {
                event_id: $scope.event.info.id,
                sum: $scope.payment_sum
            }
        ).success(function() {
            alert('ok');
            $scope.payment_sum = null;
        }).error(function() {
            alert('error');
        });
//        $scope.event.reload();
    }

};

var PrevEventContractModalCtrl = function ($scope, $modalInstance, model, $filter) {
    $scope.model = model;
    $scope.selected = {
        lcon_idx: null
    };

    $scope.format_event_period = function (event) {
        return '{0} - {1}'.formatNonEmpty($filter('asDateTime')(event.set_date), $filter('asDateTime')(event.exec_date));
    };
    $scope.format_contract_info = function (lcon) {
        return '<strong>{0}</strong>, {1}'.formatNonEmpty(lcon.number_contract || 'без номера', lcon.date_contract);
    };
    $scope.format_payer_info = function (lcon) {
        if ($scope.is_payer_org(lcon)) {
            return 'Юр. лицо:<br> {0}'.formatNonEmpty(lcon.payer_org.full_name);
        } else if ($scope.is_payer_person(lcon)) {
            return 'Физ. лицо:<br>{<strong>ФИО</strong> |0|<br>} {<strong>документ</strong> |1|<br>} {<strong>адрес</strong> |2|<br>}'.formatNonEmpty(
                '{0} {1} {2} {3| г.р.}'.formatNonEmpty(lcon.last_name, lcon.first_name, lcon.patr_name, lcon.birth_date),
                '{0}{ серия |0}{ |1}{ номер |2}'.formatNonEmpty(safe_traverse(lcon, ['doc_type', 'name']), lcon.serial_left, lcon.serial_right, lcon.number),
                '{0}'.formatNonEmpty(lcon.reg_address)
            );
        } else {
            return 'Данные плательщика отсутствуют';
        }
    };

    $scope.is_payer_person = function (lcon) {
        function isNotEmpty(val) { return val !== undefined && val !== null; }
        return (lcon &&
            [lcon.first_name, lcon.last_name, lcon.patr_name, lcon.birth_date, lcon.doc_type,
                lcon.serial_left, lcon.serial_right, lcon.number, lcon.reg_address].some(isNotEmpty)
            );
    };
    $scope.is_payer_org = function (lcon) {
        return lcon && lcon.payer_org_id;
    };
    $scope.is_older_than_year = function (event) {
        return moment(event.set_date).isBefore(moment().subtract(1, 'years'));
    };

    $scope.select_contract = function (index) {
        $scope.selected.lcon_idx = index;
    };

    $scope.contract_selected = function () {
        return $scope.selected.lcon_idx !== null && $scope.selected.lcon_idx !== undefined;
    };
    $scope.accept = function() {
        $modalInstance.close($scope.model[$scope.selected.lcon_idx].local_contract);
    };
    $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
    };
};

var RelativesModalCtrl = function ($scope, $modalInstance) {
    $scope.initialize = function() {
        $scope.relatives = $scope.event.info.client.relations.map(function (rel) {
            return rel.direct ?
            {
                name: rel.relative.full_name,
                rel_id: rel.relative.id,
                rel_type: rel.rel_type.rightName
            } :
            {
                name: rel.relative.full_name,
                rel_id: rel.relative.id,
                rel_type: rel.rel_type.leftName
            };
        });
        $scope.selected = {
            client_id: null
        };
    };
    $scope.accept = function() {
        $modalInstance.close($scope.selected.client_id);
    };
    $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
    };

    $scope.initialize();
};

var SwitchPayerModalCtrl = function ($scope, $modalInstance, from_tab) {
    $scope.from_tab = from_tab;
    $scope.accept = function() {
        $modalInstance.close();
    };
    $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
    };
};
var EventServicesCtrl = function($scope, $http) {
    $scope.query = "";
    $scope.found_services = null;
    $scope.search_processed = false;

    $scope.perform_search = function(val) {
        $scope.search_processed = false;
        if (!val) {
            $scope.found_services = null;
        } else {
            $http.get(
                url_for_event_api_search_services, {
                    params: {
                        q: val,
                        client_id: $scope.event.info.client_id,
                        event_type_id: $scope.event.info.event_type.id,
                        contract_id: $scope.event.info.contract ? $scope.event.info.contract.id : null,
                        person_id: $scope.event.info.exec_person ? $scope.event.info.exec_person.id : null
                    }
                }
            ).success(function (data) {
                $scope.found_services = data.result;
                $scope.search_processed = true;
            });
        }
    };

    $scope.query_clear = function() {
        $scope.found_services = null;
        $scope.query = '';
    };


    // ng-class="{'success': service.fully_paid || (service.is_new && service.coord_person_id) || (!service.is_new && service.coord_actions && service.coord_actions.length==service.amount),
    // 'warning': service.partially_paid || (!service.is_new && service.coord_actions && service.coord_actions.length<service.amount),
    // 'info': service.is_new && !(service.is_new && service.coord_person_id),
    // 'danger': !service.fully_paid && !service.partially_paid && !service.is_new && !service.coord_actions.length}"
    $scope.get_class = function (service) {
        var result = [];
        if (service.check_payment() || service.check_coord()) {
            result.push('success');
        } else if (service.check_payment('partial') || service.check_coord('partial')) {
            result.push('warning');
        } else {
            result.push(service.is_new() ? 'info' : 'danger');
        }
        return result;
    };

    $scope.$on('event_loaded', function() {
        $scope.query_clear();
    });
    $scope.$on('eventFormStateChanged', function() {
        $scope.query_clear();
    });

};

var EventInfoCtrl = function ($scope, WMEvent, $http, RefBookService, $window, $document, PrintingService, Settings,
        $filter, $modal, $interval, ActionTypeTreeModal, WMEventServices, WMEventFormState, MessageBox) {
    $scope.aux = aux;
    $scope.current_role_maybe = current_user.current_role_maybe;
    $scope.Organisation = RefBookService.get('Organisation');
    $scope.Settings = new Settings();
    $scope.alerts = [];
    $scope.eventServices = WMEventServices;
    $scope.formstate = WMEventFormState;

    var params = aux.getQueryParams(location.search);
    $scope.event_id = params.event_id;
    $scope.client_id = params.client_id;
    $scope.ticket_id = params.ticket_id;
    var event = $scope.event = new WMEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.editing = {
        submit_attempt: false
    };

    $scope.initialize = function() {
        $scope.event.reload().
            then(function() {
                $scope.$broadcast('event_loaded');
                $scope.formstate.set_state(event.info.event_type.request_type, event.info.event_type.finance, event.is_new());
                if (!$scope.event.is_new()) {
                    $scope.ps.set_context($scope.event.info.event_type.print_context);
                }

                $scope.$watch(function () {
                    return [event.info.event_type.request_type, event.info.event_type.finance];
                }, function (n, o) {
                    if (n !== o) {
                        var rt = n[0],
                            fin = n[1];
                        $scope.formstate.set_state(rt, fin, event.is_new());
                        $scope.$broadcast('eventFormStateChanged', {
                            request_type: rt,
                            finance: fin
                        });
                    }
                }, true);
            });
    };

    $scope.open_action_tree = function (at_class) {
        ActionTypeTreeModal.open(at_class, $scope.event_id, $scope.event.info.client.info)
            .result.then(function (result) {
                if(typeof (result) === 'object'){
                    $scope.child_window = result;
                } else {
                    $scope.event.reload();
                }
            });
    };

    $scope.save_event = function (close_event) {
        if (typeof (close_event) === 'undefined') {
            close_event = false;
        }
        $scope.editing.submit_attempt = true;
        if ($scope.eventForm.$valid) {
            $scope.event.save(close_event).
                then(function (result) {
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
                        $scope.event.reload().then(function () {
                            $scope.$broadcast('event_loaded');
                        });
                    }
                    if (close_event) {
                        alert("Обращение закрыто");
                    }
                }, function (message) {
                    alert(message);
                });
        } else {
            var formelm = $('#eventForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
        }
    };

    $scope.delete_event = function () {
        if($scope.event_has_payments()) {
            alert('Невозможно удалить обращение! По нему была совершена оплата.');
            return;
        }
        MessageBox.question(
            'Удаление обращения',
            'Вы уверены, что хотите удалить текущее обращение?'
        ).then(function () {
            $scope.eventServices.delete_event(
                event
            ).then(function () {
                if (window.opener) {
                    window.opener.focus();
                    window.close();
                }
            }, function (response) {
                var rr = response.result;
                var message = rr.name + ': ' + (rr.data ? rr.data.err_msg : '');
                alert(message);
            });
        });
    };

    $scope.event_mandatoryResult = function() {
        return $scope.Settings.get_string('Event.mandatoryResult') == '1';
    };

    $scope.event_check_results = function() {
        if (!$scope.event.info.result){
            alert("Необходимо задать результат");
            return false
        }
        if (!$scope.formstate.is_diagnostic() && !$scope.event.info.ache_result && $scope.event_mandatoryResult()){
            alert("Необходимо задать исход заболевания/госпитализации");
            return false
        }
        return true;
    };
    $scope.event_check_final_diagnosis = function() {
        var final_diagnosis = $scope.event.get_final_diagnosis()
        if (!final_diagnosis){
            alert("Необходимо указать заключительный диагноз.");
            return false
        } else if (final_diagnosis.length > 1){
            alert("В обращении не может быть больше одного заключительного диагноза.");
            return false
        }
        if(!final_diagnosis[0].result){
            alert("Необходимо указать результат заключительного диагноза");
            return false
        }
        return true
    };

    $scope.event_has_payments = function () {
        return $scope.event.payment && $scope.event.payment.payments.payments.length;
    };
    $scope.btn_delete_event_visible = function () {
        return !$scope.event.is_new() && $scope.event.payment && !$scope.event_has_payments();
    };

    $scope.open_unclosed_actions_modal = function(unclosed_actions) {
        var modalInstance = $modal.open({
            templateUrl: 'modal-unclosed-actions.html',
            controller: UnclosedActionsModalCtrl,
            resolve: {
                unclosed_actions: function(){
                    return unclosed_actions;
                }
            },
            scope: $scope
        });
        modalInstance.result.then(function () {
            $scope.save_event(true);
        });
    };

    $scope.delete_action = function (action) {
        MessageBox.question(
            'Удаление записи',
            'Вы уверены, что хотите удалить "{0}"?'.format(safe_traverse(action, ['name']))
        ).then(function () {
            $scope.eventServices.delete_action(
                event, action
            ).then(angular.noop, function () {
                alert('Ошибка удаления действия. Свяжитесь с администратором.');
            });
        });
    };

    $scope.close_event = function(){
        if (!$scope.event.is_closed){
            var unclosed_actions = $scope.event.get_unclosed_actions();
            if (!$scope.event_check_results()){
                return false;
            } else if (!$scope.formstate.is_diagnostic() && !$scope.event_check_final_diagnosis()){
                return false;
            } else if (unclosed_actions.length){
                $scope.open_unclosed_actions_modal(unclosed_actions);
            } else {
                $scope.save_event(true);
            }
        }
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

    $scope.filter_results = function(event_purpose) {
        return function(elem) {
            return elem.eventPurpose_id == event_purpose;
        };
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

    // todo: action data not here
    $scope.action_type_tree = [];
    $scope.action_type_popped = null;
    $scope.at_pop_toggle = function (at_class) {
        if ($scope.action_type_popped === at_class) {
            $scope.action_type_popped = null;
        } else {
            $scope.action_type_popped = at_class;
        }
    };

    $scope.hidden_nodes = [];
    $scope.toggle_vis = function (node_id) {
        if ($scope.hidden_nodes.has(node_id)) {
            $scope.hidden_nodes.splice($scope.hidden_nodes.indexOf(node_id), 1);
        } else {
            $scope.hidden_nodes.push(node_id);
        }
    };
    $scope.subtree_shown = function (node_id) {
        return !$scope.hidden_nodes.has(node_id);
    };

    $scope.open_action = function (action_id) {
        $scope.child_window = window.open(url_for_schedule_html_action + '?action_id=' + action_id);
    };

    // action data end

    $scope.$watch('event.info.contract', function(new_val, old_val) {
        if (new_val != old_val) {
            $scope.$broadcast('form_state_change', {
                finance: $scope.event.info.event_type.finance,
                contract: new_val
            });
        }
    }, true);

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
                    $scope.event.reload().then(function () {
                            $scope.$broadcast('event_loaded');
                        });
                    $scope.clearInterval();
                    $scope.child_window = {};
                }
            }, 500);
        }
    });

    $scope.initialize();
};

var UnclosedActionsModalCtrl = function ($scope, $modalInstance, unclosed_actions) {
    $scope.unclosed_actions = unclosed_actions;
    $scope.accept = function() {
        $modalInstance.close();
    };
    $scope.cancel = function() {
        $modalInstance.dismiss('cancel');
    };
};

WebMis20.controller('EventDiagnosesCtrl', ['$scope', 'RefBookService', '$http', EventDiagnosesCtrl]);
WebMis20.controller('EventMainInfoCtrl', ['$scope', '$http', 'RefBookService', 'EventType', '$window', '$timeout', 'Settings', '$modal', '$filter', EventMainInfoCtrl]);
WebMis20.controller('EventPaymentCtrl', ['$scope', 'RefBookService', 'Settings', '$http', '$modal', EventPaymentCtrl]);
WebMis20.controller('EventServicesCtrl', ['$scope', '$http', EventServicesCtrl]);
WebMis20.controller('EventInfoCtrl', ['$scope', 'WMEvent', '$http', 'RefBookService', '$window', '$document', 'PrintingService', 'Settings', '$filter', '$modal', '$interval', 'ActionTypeTreeModal', 'WMEventServices', 'WMEventFormState', 'MessageBox', EventInfoCtrl]);
