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

    $scope.$on('event_loaded', function() {
        if ($scope.event.is_new()) $scope.event.info.set_date = new Date($scope.event.info.set_date);

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

    $scope.check_oms = function(){
        var policy = $scope.event.info.client.compulsory_policy;
        if (!policy){
            $scope.add_policy_error('У пациента не указан полис ОМС');
        } else {
            if (!policy.beg_date || moment(policy.beg_date).isAfter($scope.event.info.set_date)) {
                $scope.add_policy_error('Дата начала действия полиса не установлена или превышает дату создания обращения');
            }
            if (!policy.end_date || moment($scope.event.info.set_date).isAfter(policy.end_date)) {
                $scope.add_policy_error('Не установлена дата окончания действия полиса или дата создания обращения превышает её');
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
    $scope.payer_is_person = function() {
        function isDefined(element) {
            return element !== undefined && element !== null;
        }
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return (lc !== null &&
            [lc.first_name, lc.last_name, lc.patr_name, lc.birth_date, lc.doc_type,
                lc.serial_left, lc.serial_right, lc.number, lc.reg_address].some(isDefined)
            );
    };
    $scope.payer_is_org = function() {
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return lc !== null && lc.payer_org;
    };
    $scope.person_tab_active = function() { return !event_created || $scope.payer_is_person(); };
    $scope.org_tab_active = function() { return event_created && $scope.payer_is_org(); };
    $scope.integration1CODVD_enabled = function() {
        return $scope.Settings.get_string('Event.Payment.1CODVD') == '1';
    };

    $scope.formcnf = {
        tab_payer_person: {
            disabled: event_created && $scope.payer_is_org,
            active: $scope.person_tab_active()
        },
        tab_payer_org: {
            disabled: event_created && $scope.payer_is_person,
            active: $scope.org_tab_active()
        },
        payer_field: {
            disabled: event_created
        },
        contract_field: {
            disabled: event_created || $scope.integration1CODVD_enabled()
        }
    };

    $scope.$on('event_loaded', function() {
        $scope.formcnf.tab_payer_person.active = $scope.person_tab_active();
        $scope.formcnf.tab_payer_org.active = $scope.org_tab_active();
        $scope.formcnf.contract_field.disabled = event_created || $scope.integration1CODVD_enabled();
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
                    from_tab: from_tab
                }
            });

            modalInstance.result.then(function () {
                if (from_tab === 0) {
                    lc.first_name = null;
                    lc.last_name = null;
                    lc.patr_name = null;
                    lc.birth_date = null;
                    lc.doc_type = null;
                    lc.serial_left = null;
                    lc.serial_right = null;
                    lc.number = null;
                    lc.reg_address = null;
                } else {
                    lc.payer_org = null
                }
            }, function () {
                if (from_tab === 0) {
                    $scope.switch_in_process = true;
                    $scope.formcnf.tab_payer_person.active = true;
                } else {
                    $scope.switch_in_process = true;
                    $scope.formcnf.tab_payer_org.active = true;
                }
            });
        }
    };

    $scope.get_payer = function(source, client_id) {
        $http.get(url_for_event_api_new_event_payment_info_get, {
            params: {
                event_type_id: $scope.event.info.event_type.id,
                client_id: client_id,
                source: source
            }
        }).success(function(data) {
            $scope.event.payment = data.result;
        }).error(function() {
            alert('error in getting data from server');
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
                $scope.get_payer('client', selected_client_id);
            }
        });
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
var EventServicesCtrl = function($scope, $http, WMEventService) {
    $scope.query = "";
    $scope.found_services = null;
    $scope.search_processed = false;
    $scope.full_sum = 0;

    $scope.finance_is_oms = function(){return $scope._finance && $scope._finance.code == '2'};
    $scope.finance_is_dms = function(){return $scope._finance && $scope._finance.code == '3'};
    $scope.finance_is_paid = function(){return $scope._finance && $scope._finance.code == '4'};

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

    $scope.add_service = function(service) {
        if (!aux.inArray($scope.event.services, service)) {
            var service_data = angular.extend(service, {
                amount: 1,
                is_new: true,
                sum: service.price,
                actions: [],
                coord_actions: [],
                coord_count: 0,
                account: true
            });
            $scope.event.services.push(new WMEventService(service_data, $scope.event.payment.payments));
        }
    };

    $scope.remove_service = function(index) {
        var service = $scope.event.services[index];
        if (service.actions.length) {
            $http.post(
                url_for_event_api_service_delete_service, {
                    event_id: $scope.event.info.id,
                    action_id_list: service.actions
                }
            ).success(function() {
                    $scope.event.services.splice(index, 1);
                }).error(function() {
                    alert('error');
                });
        } else {
            $scope.event.services.splice(index, 1);
        }
    };

    $scope.$watch('event.services', function(new_val, old_val) {
        if (new_val) {
            $scope.full_sum = new_val.map(function(service) {
                return service.price * service.amount;
            }).reduce(function(prev_val, cur_val) {
                return prev_val + cur_val;
            }, 0);

            var payment = $scope.event.payment;
            $scope.paid_sum = payment && payment.payments.map(function(payment) {
                return payment.sum + payment.sum_discount;
            }).reduce(function(prev_val, cur_val) {
                return prev_val + cur_val;
            }, 0) || 0;
        }
    }, true);

    $scope.$on('form_state_change', function(event, arg) {
        $scope._finance = arg['finance'];
        $scope._contract = arg['contract'];
        $scope.query_clear();
    });

    $scope.pay = function(service) {
        var act_to_pay = null;
        var paid_actions = $scope.event.payment.payments.map(function(p) {
            return p.action_id;
        });
        service.actions.forEach(function(a_id) {
            if (act_to_pay === null && (paid_actions.indexOf(a_id) == -1)) {
                act_to_pay = a_id;
            }
        });
        if (act_to_pay) {
            $http.post(
                url_for_event_api_service_make_payment, {
                    event_id: $scope.event.info.id,
                    service_id: service.service_id,
                    action_id: act_to_pay,
                    sum: service.price
                }
            ).success(function() {
                    // alert('ok');#}
                }).error(function() {
                    alert('error');
                });
        }
        $scope.event.reload();
    };

    $scope.apply_coord_service = function(service) {
        if ($scope.event.info.id){
            service.coord_person_id = current_user_id;
            $http.post(
                url_for_event_api_service_add_coord, {
                    event_id: $scope.event.info.id,
                    finance_id: $scope.event.info.contract.finance.id,
                    service: service
                }
            ).success(function(result) {
                    service.actions = result['result']['data'];
                    service.coord_actions = result['result']['data'];
                    service.coord_count = service.coord_actions.length;
                    // alert('ok');#}
                }).error(function() {
                    service.coord_person_id = undefined;
                    alert('error');
                });
        } else {
            service.coord_person_id = current_user_id;
            service.coord_count = service.amount;
        }
        // $scope.event.reload();#}
    };

    $scope.remove_coord_service = function(service) {
        if ($scope.event.info.id){
            $http.post(
                url_for_event_api_service_remove_coord, {
                    action_id: service.coord_actions,
                    coord_person_id: null
                }
            ).success(function() {
                    service.coord_actions = [];
                    service.coord_person_id = null;
                    service.coord_count = service.coord_actions.length;
                    // alert('ok');#}
                }).error(function() {
                    alert('error');
                });
        } else {
            service.coord_actions = [];
            service.coord_person_id = null;
            service.coord_count = service.coord_actions.length;
        }
        // $scope.event.reload();#}
    };

    $scope.change_account_service = function(service) {
        service.account = !service.account
        if ($scope.event.info.id && service.actions.length){
            $http.post(
                url_for_event_api_service_change_account, {
                    actions: service.actions,
                    account: service.account
                }
            ).error(function() {
                    alert('error');
                });
        }
    };
};

var EventInfoCtrl = function ($scope, WMEvent, $http, RefBookService, $window, PrintingService, Settings, $filter, $modal, ActionTypeTreeModal) {
    $scope.aux = aux;
    $scope.current_role_maybe = current_user.current_role_maybe;
    $scope.Organisation = RefBookService.get('Organisation');
    $scope.Settings = new Settings();
    $scope.alerts = [];

    var params = aux.getQueryParams(location.search);
    $scope.event_id = params.event_id;
    $scope.client_id = params.client_id;
    $scope.ticket_id = params.ticket_id;
    $scope.event = new WMEvent($scope.event_id, $scope.client_id, $scope.ticket_id);
    $scope.editing = {
        submit_attempt: false
    };
    $scope.policies = [];

    $scope.initialize = function() {
        $scope.event.reload().
            then(function() {
                $scope.$broadcast('event_loaded');
                if ($scope.event.is_new()) {

                } else {
                    $scope.ps.set_context($scope.event.info.event_type.print_context)
                }

                if ($scope.event.info.client.info.birth_date) {
                    $scope.event.info.client.info.age = moment().diff(moment($scope.event.info.client.info.birth_date), 'years');
                }
                if ($scope.event.info.client.compulsory_policy && $scope.event.info.client.compulsory_policy.policy_text) {
                    $scope.policies.push($scope.event.info.client.compulsory_policy.policy_text + ' ('+ $filter('asDate')($scope.event.info.client.compulsory_policy.beg_date) + '-' + $filter('asDate')($scope.event.info.client.compulsory_policy.end_date) +')');
                }
                if ($scope.event.info.client.voluntary_policies.length>0) {
                    angular.forEach($scope.event.info.client.voluntary_policies, function (value, key) {
                        $scope.policies.push(value.policy_text + ' ('+ $filter('asDate')(value.beg_date) + '-' + $filter('asDate')(value.end_date) + ')');
                    });
                }
            });
    };

    $scope.open_action_tree = function (at_class) {
        ActionTypeTreeModal.open(at_class, $scope.event_id, $scope.event.info.client.info);
    };

    $scope.save_event = function (close_event) {
        if (typeof (close_event) === 'undefined') {
            close_event = false;}
        $scope.editing.submit_attempt = true;
        if ($scope.eventForm.$valid) {
            $scope.event.save(close_event).
                then(function (event_id) {
                    $scope.eventForm.$setPristine();
                    if ($scope.event.is_new()) {
                        $window.open(url_for_event_html_event_info + '?event_id=' + event_id, '_self');
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

        }
    };

    $scope.event_mandatoryResult = function() {
        return $scope.Settings.get_string('Event.mandatoryResult') == '1';
    };

    $scope.event_check_results = function() {
        if (!$scope.event.info.result){
            alert("Необходимо задать результат");
            return false
        }
        if (!$scope.event.info.ache_result && $scope.event_mandatoryResult()){
            alert("Необходимо задать исход заболевания/госпитализации");
            return false
        }
        return true;
    };
    $scope.event_check_final_diagnosis = function() {
        if (!$scope.event.get_final_diagnosis()){
            alert("Необходимо указать заключительный диагноз");
            return false
        }
        return true
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

    $scope.close_event = function(){
        if (!$scope.event.is_closed){
            var unclosed_actions = $scope.event.get_unclosed_actions();
            if (!$scope.event_check_results()){
                return false;
            } else if (!$scope.event_check_final_diagnosis()){
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

    $scope.print_template = function (template_id) {
        $http.post(
            url_print_subsystem, {
                id: template_id,
                context_type: "event",
                event_id: $scope.event_id,
                additional_context: {
                    currentOrgStructure: "",
                    currentOrganisation: 3479,
                    currentPerson:"1"
                }
            }).success(function (data) {
                var w = $window.open();
                w.document.open();
                w.document.write(data);
                w.document.close();
                w.print();
            })
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
        if (aux.inArray($scope.hidden_nodes, node_id)) {
            $scope.hidden_nodes.splice($scope.hidden_nodes.indexOf(node_id), 1);
        } else {
            $scope.hidden_nodes.push(node_id);
        }
    };
    $scope.subtree_shown = function (node_id) {
        return !aux.inArray($scope.hidden_nodes, node_id);
    };

    $scope.open_action = function (action_id) {
        window.open(url_for_schedule_html_action + '?action_id=' + action_id);
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
WebMis20.controller('EventServicesCtrl', ['$scope', '$http', 'WMEventService', EventServicesCtrl]);
WebMis20.controller('EventInfoCtrl', ['$scope', 'WMEvent', '$http', 'RefBookService', '$window', 'PrintingService', 'Settings', '$filter', '$modal', 'ActionTypeTreeModal', EventInfoCtrl]);
