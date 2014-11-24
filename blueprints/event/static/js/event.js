/**
 * Created by mmalkov on 11.07.14.
 */
var EventDiagnosesCtrl = function ($scope) {
};
var EventMainInfoCtrl = function ($scope, $http, RefBookService, EventType, $window, $timeout, Settings, $modal, $filter) {
    $scope.Organisation = RefBookService.get('Organisation');
    $scope.Contract = RefBookService.get('Contract');
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.rbFinance = RefBookService.get('rbFinance');
    $scope.rbEventType = new EventType();
    $scope.OrgStructure = RefBookService.get('OrgStructure');
    $scope.rbResult = RefBookService.get('rbResult');
    $scope.rbAcheResult = RefBookService.get('rbAcheResult');

    var event_created = !$scope.event.is_new();
    $scope.widget_disabled = function (widget_name) {
        if (['request_type', 'finance', 'contract', 'event_type', 'dms',
             'exec_person', 'org_structure', 'set_date'
        ].has(widget_name)
        ) {
            return event_created || $scope.event.ro;
        } else if (widget_name === 'exec_person') {
            return event_created || $scope.event.ro || !current_user.current_role_maybe('admin', 'rRegistartor', 'clinicRegistrator');
        } else if (['result', 'ache_result'].has(widget_name)) {
            return $scope.event.ro || current_user_id !== safe_traverse($scope.event, ['info', 'exec_person', 'id']);
        } else if (['exec_date'].has(widget_name)) {
            return $scope.event.ro;
        }
    };
    $scope.services_added = function () {
        return $scope.event.is_new() && $scope.event.services.length;
    };
    $scope.cmb_result_available = function () {
        return current_user.current_role_maybe('admin', 'doctor', 'clinicDoctor') || (
            current_user.current_role_maybe('rRegistartor', 'clinicRegistrator') && $scope.formstate.is_diagnostic()
        );
    };
    $scope.cmb_ache_result_available = function () {
        return current_user.current_role_maybe('admin', 'doctor', 'clinicDoctor');
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
//            $scope.finance.selected = $scope.rbFinance.get_by_code(4);
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
var EventPaymentCtrl = function($scope, RefBookService, Settings, $http, $modal, MessageBox) {
    $scope.rbDocumentType = RefBookService.get('rbDocumentType');

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
        return $scope.event.ro;
    };
    $scope.contract_info_disabled = function () {
        return event_created || $scope.integration1CODVD_enabled();
    };
    $scope.btn_edit_contract_info_visible = function () {
        var lc = $scope.event.payment && $scope.event.payment.local_contract || null;
        return !(lc && lc.date_contract && lc.number_contract || $scope.integration1CODVD_enabled() || $scope.event.ro);
    };
    $scope.import_payer_btn_disabled = function () {
        return $scope.event.ro;
    };
    $scope.btn_delete_lc_disabled = function () {
        return $scope.event.ro;
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
        $scope.payer_tabs.person.disabled = $scope.event.ro; //event_created && $scope.payer_tabs.org.active;
        $scope.payer_tabs.org.disabled = $scope.event.ro; // event_created && $scope.payer_tabs.person.active;
    };

    $scope.contract_available = function () {
        var event = $scope.event;
        return event.payment && event.payment.local_contract && event.payment.local_contract.id;
    };
    $scope.payer_info_filled = function () {
        return $scope.payer_is_person() || $scope.payer_is_org();
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

    $scope.import_payer_info = function (from) {
        function process_import() {
            if (from === 'self') {
                $scope.get_payer($scope.event.info.client_id);
            } else if (from === 'parent') {
                $scope.open_relatives_modal();
            } else if (from === 'prev') {
                $scope.open_prev_event_contract_modal();
            }
        }
        if ($scope.payer_info_filled()) {
            MessageBox.question(
                'Изменение данных плательщика',
                'Данные плательщика будут изменены. Продолжить?'
            ).then(function () {
                process_import();
            });
        } else {
            process_import();
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
                windowClass: 'modal-scrollable',
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

    $scope.search_disabled = function () {
        return $scope.event.ro;
    };
};

var EventInfoCtrl = function ($scope, WMEvent, $http, RefBookService, $window, $document, PrintingService, Settings,
        $filter, $modal, WMEventServices, WMEventFormState, MessageBox) {
    $scope.aux = aux;
    $scope.current_role_maybe = current_user.current_role_maybe;
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

    $scope.save_event = function () {
        $scope.editing.submit_attempt = true;
        if ($scope.eventForm.$valid) {
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
            }, function (message) {
                MessageBox.info('Ошибка сохранения', message);
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

    $scope.event_has_payments = function () {
        return $scope.event.payment && $scope.event.payment.payments.payments.length;
    };
    $scope.btn_delete_event_visible = function () {
        return !$scope.event.is_new() && $scope.event.payment && !$scope.event_has_payments();
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

    $scope.filter_results = function(event_purpose) {
        return function(elem) {
            return elem.eventPurpose_id == event_purpose;
        };
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

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

WebMis20.controller('EventDiagnosesCtrl', ['$scope', 'RefBookService', '$http', EventDiagnosesCtrl]);
WebMis20.controller('EventMainInfoCtrl', ['$scope', '$http', 'RefBookService', 'EventType', '$window', '$timeout', 'Settings', '$modal', '$filter', EventMainInfoCtrl]);
WebMis20.controller('EventPaymentCtrl', ['$scope', 'RefBookService', 'Settings', '$http', '$modal', 'MessageBox', EventPaymentCtrl]);
WebMis20.controller('EventServicesCtrl', ['$scope', '$http', EventServicesCtrl]);
WebMis20.controller('EventInfoCtrl', ['$scope', 'WMEvent', '$http', 'RefBookService', '$window', '$document', 'PrintingService', 'Settings', '$filter', '$modal', 'WMEventServices', 'WMEventFormState', 'MessageBox', EventInfoCtrl]);
