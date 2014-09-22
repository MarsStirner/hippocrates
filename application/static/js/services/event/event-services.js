'use strict';

angular.module('WebMis20.services').
    service('WMEventServices', ['$http', '$injector', '$q', function ($http, $injector, $q) {
        function contains_sg (event, at_id, service_id) {
            return event.services.some(function (sg) {
                return sg.at_id === at_id && (sg.service_id !== undefined ? sg.service_id === service_id : true);
            });
        }

        return {
            add_service: function(event, service_group) {
                if (!contains_sg(event, service_group.at_id, service_group.service_id)) {
                    var service_data = angular.extend(
                            service_group,
                            {
                                amount: 1,
                                sum: service_group.price,
                                actions: [undefined]
                            }
                        ),
                        SgModel = $injector.get('WMEventServiceGroup');
                    event.services.push(new SgModel(service_data, event.payment.payments));
                }
            },
            remove_service: function(event, sg_idx) {
                if (!confirm('Вы действительно хотите удалить выбранную группу услуг?')) {
                    return;
                }
                var sg = event.services[sg_idx];
                var action_id_list = sg.actions.map(function (a) {
                    return a.action_id;
                });
                var group_saved = action_id_list.length && action_id_list.every(function (a_id) {
                    return a_id !== undefined && a_id !== null;
                });
                if (group_saved) {
                    $http.post(
                        url_for_event_api_service_delete_service, {
                            event_id: event.info.id,
                            action_id_list: action_id_list
                        }
                    ).success(function() {
                        event.services.splice(sg_idx, 1);
                    }).error(function() {
                        alert('error');
                    });
                } else {
                    event.services.splice(sg_idx, 1);
                }
            },
            remove_action: function (event, action, sg) {
                if (action.action_id && !confirm('Вы действительно хотите удалить выбранную услугу?')) {
                    return;
                }
                var sg_idx = event.services.indexOf(sg),
                    action_idx = event.services[sg_idx].actions.indexOf(action),
                    self = this;
                if (action.action_id) {
                    $http.post(
                        url_for_event_api_service_delete_service, {
                            action_id_list: [action.action_id]
                        }
                    ).success(function () {
                        sg.actions.splice(action_idx, 1);
                        if (!sg.actions.length) {
                            self.remove_service(event, sg_idx)
                        }
                    }).error(function () {
                        alert('error');
                    });
                } else {
                    sg.actions.splice(action_idx, 1);
                    if (!sg.actions.length) {
                        self.remove_service(event, sg_idx)
                    }
                }
            },
            coordinate: function (action, off) {
                var user = off ? null : {id: current_user_id},
                    date = off ? null : new Date();
                if ((action.is_coordinated() && off) || (!action.is_coordinated() && !off)) {
                    action.coord_person = user;
                    action.coord_date = date;
                }
            },
            update_payment: function (event, payment) {
                var PlModel = $injector.get('WMEventPaymentList');
                var cur_lc = event.payment.local_contract;
                if (cur_lc.date_contract && !payment.local_contract.date_contract) {
                    payment.local_contract.date_contract = cur_lc.date_contract;
                }
                if ((cur_lc.number_contract !== null || cur_lc.number_contract !== undefined) &&
                    !payment.local_contract.number_contract) {
                    payment.local_contract.number_contract = cur_lc.number_contract;
                }
                event.payment = {
                    local_contract: payment.local_contract,
                    payments: new PlModel(payment.payments)
                };
            },
            get_action_ped: function (action_type_id) {
                var deferred = $q.defer();
                $http.get(url_api_get_action_ped, {
                    params: {
                        action_type_id: action_type_id
                    }
                }).success(function (data) {
                    deferred.resolve(new Date(data.result.ped));
                }).error(function (response) {
                    deferred.reject();
                });
                return deferred.promise;
            },
            add_new_diagnosis: function () {
                return {
                        "id": null,
                        "set_date": null,
                        "end_date": null,
                        "diagnosis_type": null,
                        "diagnosis": {
                            "id": null,
                            "mkb": null,
                            "mkbex": null,
                            "client_id": null
                        },
                        "character": null,
                        "person": null,
                        "notes": null,
                        "action_id": null,
                        "result": null,
                        "ache_result": null,
                        "health_group": null,
                        "trauma_type": null,
                        "phase": null
                    };
            },
            delete_diagnosis: function (diag_list, diagnosis, deleted) {
                if (arguments.length < 3) {
                    deleted = 1;
                }
                if (diagnosis && diagnosis.id) {
                    diagnosis.deleted = deleted;
                } else {
                    var idx = diag_list.indexOf(diagnosis);
                    diag_list.splice(idx, 1);
                }
            }
        };
    }]).
    service('WMEventFormState', [function () {
        var rt = {},
            fin = {},
            is_new = null;
        return {
            set_state: function (request_type, finance, is_new) {
                rt = request_type;
                fin = finance;
                is_new = is_new;
            },
            is_new: function () {
                return is_new;
            },
            is_policlinic: function () {
                return rt.code === 'policlinic';
            },
            is_diagnostic: function () {
                return rt.code === '4';
            },
            is_paid: function () {
                return fin.code === '4';
            },
            is_oms: function (client, type) {
                return fin.code === '2';
            },
            is_dms: function (client, type) {
                return fin.code === '3';
            }
        };
    }]);