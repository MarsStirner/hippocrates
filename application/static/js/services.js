'use strict';

angular.module('WebMis20.services', []).
    service('WMAppointment', ['$http', function ($http) {
        return {
            make: function (ticket, client_id) {
                var appointment_type_code = arguments[2];
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    appointment_type_code: appointment_type_code // Это может настраиваться
                })
            },
            cancel: function (ticket, client_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    delete: true
                })
            },
            change_notes: function (ticket_client_id, notes) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    note: notes
                })
            }
        }
    }]).
    factory('WMEvent', ['$http', '$q', 'WMEventServiceGroup', 'WMEventPaymentList',
        function($http, $q, WMEventServiceGroup, WMEventPaymentList) {
            var WMEvent = function(event_id, client_id, ticket_id) {
                this.event_id = parseInt(event_id);
                this.client_id = client_id;
                this.ticket_id = ticket_id;
                this.info = null;  //TODO: в качестве info.client заиспользовать WMClient?
                this.payment = null;
                this.diagnoses = [];
                this.services = [];
            };

            WMEvent.prototype.reload = function() {
                var self = this;
                var url = this.is_new() ? url_event_new : url_event_get;
                var params = this.is_new() ? {
                    client_id: this.client_id,
                    ticket_id: this.ticket_id
                } : {
                    event_id: this.event_id
                };
                var deferred = $q.defer();
                $http.get(url, {
                    params: params
                }).success(function (data) {
                    self.info = data.result.event;
                    if (self.info.client.live_address !== null && self.info.client.live_address.synced) {
                        self.info.client.live_address = self.info.client.reg_address;
                    }
                    self.diagnoses = data.result.diagnoses || [];

                    var p = data.result.payment;
                    self.payment = {
                        local_contract: (p && p.local_contract) ? p.local_contract : null,
                        payments: new WMEventPaymentList(p ? p.payments : [])
                    };
                    self.services = data.result.services && data.result.services.map(function(service) {
                        return new WMEventServiceGroup(service, self.payment.payments);
                    }) || [];
                    self.is_closed = self.closed();
                    deferred.resolve();
                }).
                error(function(data) {
                    deferred.reject('error load event');
                });
                return deferred.promise;
            };

            WMEvent.prototype.save = function(close_event) {
                var self = this;
                var deferred = $q.defer();
                $http.post(url_event_save, {
                    event: this.info,
                    diagnoses: this.diagnoses,
                    payment: this.payment,
                    services: this.services,
                    ticket_id: this.ticket_id,
                    close_event: close_event
                }).
                    success(function(response) {
                        var event_id = response.result.id,
                            error_text = response.result.error_text;
                        deferred.resolve({
                            event_id: event_id,
                            error_text: error_text
                        });
                    }).
                    error(function(response) {
                        var rr = response.result;
                        var message = rr.name + ': ' + (rr.data ? rr.data.err_msg : '');
                        deferred.reject(message);
                    });
                return deferred.promise;
            };

            WMEvent.prototype.get_unclosed_actions = function() {
                var unclosed_actions = [];
                this.info.actions.forEach(function(item){
                    if (item.status < 2){
                        unclosed_actions.push(item);
                    }
                });
                return unclosed_actions
            };

            WMEvent.prototype.get_final_diagnosis = function() {
                var final_diagnosis = this.diagnoses.filter(function(item){
                    return item.diagnosis_type.code == 1;
                });
                return final_diagnosis.length ? final_diagnosis : null
            };

            WMEvent.prototype.is_new = function() {
                return !this.event_id;
            };

            WMEvent.prototype.closed = function() {
                return this.info && this.info.result_id !== null && this.info.exec_date !== null;
            };

            return WMEvent;
        }
    ]).
    factory('WMEventServiceGroup', ['$rootScope', 'WMEventController', 'PrintingService',
        function($rootScope, WMEventController, PrintingService) {
            var WMSimpleAction = function (action, service_group) {
                if (!action) {
                    action = {
                        action_id: null,
                        account: null,
                        amount: 1,
                        beg_date: null,
                        end_date: null,
                        status: null,
                        coord_date: null,
                        coord_person: null,
                        sum: service_group.price,
                        assigned: service_group.all_assigned !== false ?
                            service_group.all_assigned :
                            service_group.assignable.map(function (prop) {
                                return prop[0];
                            }),
                        planned_end_date: new Date()
                    }
                }
                angular.extend(this, action);
                this.planned_end_date = aux.safe_date(this.planned_end_date);
                this._is_paid_for = undefined;
            };
            WMSimpleAction.prototype.is_paid_for = function () {
                return this._is_paid_for;
            };
            WMSimpleAction.prototype.is_coordinated = function () {
                return Boolean(this.coord_person && this.coord_person.id && this.coord_date);
            };
            WMSimpleAction.prototype.is_closed = function () {
                return this.status === 2;
            };

            var WMEventServiceGroup = function(service_data, payments) {
                if (service_data === undefined) {
                    service_data = {
                        at_id: null,
                        at_code: null,
                        at_name: null,
                        service_id: undefined,
                        service_name: null,
                        actions: [],
                        price: undefined,
                        is_lab: null,
                        print_context: null,
                        assignable: [], // info list of assignable properties
                        all_assigned: [], // [] - all have same assignments, False - have different assignments
                        all_planned_end_date: null // date - all have same dates, False - have different dates
                    };
                }
                this.all_actions_closed = undefined;
                this.total_sum = undefined;
                this.account_all = undefined; // false - none, true - all, null - some
                this.coord_all = undefined;
                this.fully_paid = undefined;
                this.partially_paid = undefined;
                this.paid_count = undefined;
                this.coord_count = undefined;
                this.print_services = [];

                this.initialize(service_data, payments);
            };

            WMEventServiceGroup.prototype.initialize = function (service_data, payments) {
                var self = this;
                angular.extend(this, service_data);
                if (this.all_planned_end_date !== false) {
                    this.all_planned_end_date = aux.safe_date(this.all_planned_end_date);
                }
                this.actions = this.actions.map(function (act) {
                    return new WMSimpleAction(act, self);
                });
                this.all_actions_closed = this.actions.every(function (act) {
                    return act.is_closed();
                });
                this.actions.forEach(function (act) {
                    var ps = new PrintingService("action");
                    if (self.print_context) {
                        ps.set_context(self.print_context);
                    }
                    self.print_services.push(ps);
                });

                // many much watches
                $rootScope.$watch(function () {
                    return self.total_amount;
                }, function (n, o) {
                    self.rearrange_actions();
                    self.recalculate_sum();
                });
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.amount;
                    });
                }, function (n, o) {
                    if (n !== o) {
                        self.recalculate_amount();
                    }
                }, true);
                $rootScope.$watch(function () {
                    return self.account_all;
                }, function (n, o) {
                    if (o === undefined || n === null) {
                        return;
                    }
                    self.actions.forEach(function (act) {
                        if (act.account !== n && !act.is_closed()) {
                            act.account = n;
                            if (n) {
                                self.payments.add_charge(act);
                            } else {
                                self.payments.remove_charge(act);
                            }
                        }
                    });
                });
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.account;
                    });
                }, function (n, o) {
                    var total_count = n.length,
                        account_count = 0;
                    n.forEach(function (acc) {
                        if (acc) {
                            account_count += 1;
                        }
                    });
                    self.account_all = (account_count === total_count) ? true :
                        (account_count === 0) ? false : null;
                }, true);
                $rootScope.$watch(function () {
                    return self.coord_all;
                }, function (n, o) {
                    if (n === undefined || n === null) {
                        return;
                    }
                    self.actions.forEach(function (act) {
                        if (!act.is_coordinated() && !act.is_closed()) {
                            WMEventController.coordinate(act, !n);
                        }
                    });
                }, true);
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.coord_person ? act.coord_person.id : null;
                    });
                }, function (n, o) {
                    var total_count = n.length;
                    self.refresh_coord_info();
                    self.coord_all = (total_count === self.coord_count) ? true :
                        (self.coord_count === 0) ? false : null;
                }, true);
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return [act.assigned, act.planned_end_date];
                    });
                }, function (n, o) {
                    var asgn_list = n.map(function (data) {
                            return data[0];
                        }),
                        ref_asgn_list = asgn_list[0],
                        ped = n.map(function (data) {
                            return data[1];
                        }),
                        ref_ped = ped[0],
                        all_same_asgn = asgn_list.every(function (asgn_list) {
                            return angular.equals(asgn_list, ref_asgn_list);
                        }),
                        all_same_ped = ped.every(function (ped) {
                            return moment(ped).isSame(ref_ped);
                        });
                    self.all_assigned = all_same_asgn && ref_asgn_list;
                    self.all_planned_end_date = all_same_ped && ref_ped;
                }, true);

                this.recalculate_amount();

                if (this.price && payments) {
                    this.payments = payments;
                    this.actions.forEach(function (act) {
                        if (act.account) {
                            self.payments.add_charge(act);
                        }
                    });
                    $rootScope.$watch(function () {
                        return self.payments.charges;
                    }, function (n, o) {
                        self.refresh_payments();
                    }, true);
                }
            };

            WMEventServiceGroup.prototype.is_new = function () {
                return this.actions.some(function (a) {
                    return !a.action_id;
                });
            };

            WMEventServiceGroup.prototype.check_payment = function (type) {
                if (!arguments.length) {
                    type = 'full';
                }
                if (type === 'full') {
                    return this.actions.every(function (a) {
                        return a.is_paid_for();
                    });
                } else if (type === 'partial') {
                    return this.actions.some(function (a) {
                        return a.is_paid_for();
                    });
                }
                return false;
            };

            WMEventServiceGroup.prototype.check_coord = function (type) {
                if (!arguments.length) {
                    type = 'full';
                }
                if (type === 'full') {
                    return this.actions.every(function (a) {
                        return a.is_coordinated();
                    });
                } else if (type === 'partial') {
                    return this.actions.some(function (a) {
                        return a.is_coordinated();
                    });
                }
                return false;
            };

            WMEventServiceGroup.prototype.rearrange_actions = function () {
                var self = this,
                    total_amount = this.total_amount,
                    actions_amount = this.actions.reduce(function (sum, cur_act) {
                        return sum + cur_act.amount;
                    }, 0);
                if (actions_amount < total_amount) {
                    for (var i = 0; i < total_amount - actions_amount; i++) {
                        this.actions.push(new WMSimpleAction(null, self));
                    }
                } else if (total_amount < actions_amount) {
                    var i = actions_amount - total_amount,
                        idx = this.actions.length - 1,
                        cur_act;
                    while (i--) {
                        cur_act = this.actions[idx];
                        if (cur_act.action_id || cur_act.account) {
                            break;
                        }
                        if (cur_act.amount > 1) {
                            cur_act.amount -= 1;
                        } else {
                            this.actions.splice(idx, 1);
                            idx--;
                        }
                    }
                }
            };

            WMEventServiceGroup.prototype.recalculate_amount = function () {
                this.total_amount = this.actions.reduce(function (sum, cur_act) {
                    return sum + cur_act.amount;
                }, 0);
            };

            WMEventServiceGroup.prototype.recalculate_sum = function () {
                var self = this;
                this.actions.forEach(function (act) {
                    act.sum = act.amount * self.price;
                });
                this.total_sum = this.actions.reduce(function (sum, cur_act) {
                    return sum + cur_act.sum;
                }, 0);
            };

            WMEventServiceGroup.prototype.refresh_payments = function() {
                var total_count = this.total_amount,
                    paid_actions = this.payments.charges.filter(function (ch) {
                        return ch.suffice;
                    }).map(function (ch) {
                        return ch.action;
                    }),
                    paid_count = 0;

                this.actions.forEach(function (act) {
                    if (paid_actions.has(act)) {
                        act._is_paid_for = true;
                        paid_count += act.amount;
                    } else {
                        act._is_paid_for = false;
                    }
                });

                this.paid_count = paid_count;
                this.fully_paid = total_count === paid_count;
                this.partially_paid = paid_count > 0 && paid_count < total_count;
            };

            WMEventServiceGroup.prototype.refresh_coord_info = function () {
                var total_count = this.total_amount,
                    coordinated_count = this.actions.reduce(function (sum, cur_act) {
                        return sum + (cur_act.is_coordinated() ? cur_act.amount : 0);
                    }, 0);
                this.coord_count = coordinated_count;
                this.fully_coord = total_count === coordinated_count;
                this.partially_coord = coordinated_count > 0 && coordinated_count < total_count;
            };

            return WMEventServiceGroup;
        }
    ]).
    factory('WMEventPaymentList', [
        function() {
            var WMEventPaymentList = function (payment_data) {
                this.payments = payment_data;
                this.charges = [];
                this.total_in = null;
                this.total_out = null;
                this.diff = null;
                this.refresh();
            };
            WMEventPaymentList.prototype.add_charge = function (action) {
                this.charges.push({
                    action: action
                });
                this.refresh();
            };
            WMEventPaymentList.prototype.remove_charge = function (action) {
                var idx = -1,
                    i,
                    cur_action;
                for (i = 0; i < this.charges.length; i++) {
                    cur_action = this.charges[i].action;
                    if (cur_action === action) {
                        idx = i;
                        break;
                    }
                }
                if (idx !== -1) {
                    this.charges.splice(idx, 1);
                    this.refresh();
                }
            };
            WMEventPaymentList.prototype.refresh = function () {
                var bank = this.total_in;
                this.charges.sort(function (a, b) {
                    var a = a.action,
                        b = b.action;
                    if (a.action_id) {
                        if (b.action_id) {
                            return a.beg_date > b.beg_date ?
                                1 :
                                (a.beg_date === b.beg_date ? (a.action_id > b.action_id ? 1 : -1) : -1);
                        }
                    } else {
                        return -1;
                    }
                    return -1;
                }).forEach(function (ch) {
                    ch.suffice = bank >= ch.action.sum;
                    bank -= ch.action.sum;
                });

                this.total_in = this.payments.reduce(function (sum, cur_pay) {
                    return sum + cur_pay.sum;
                }, 0);

                this.total_out = this.charges.reduce(function (sum, cur_ch) {
                    return sum + cur_ch.action.sum;
                }, 0);

                this.diff = this.total_out - this.total_in;
            };
            return WMEventPaymentList;
        }
    ]).
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
    }]).
    service('WMEventController', ['$http', '$injector', function ($http, $injector) {
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
    service('MessageBox', ['$modal', function ($modal) {
        return {
            info: function (head, message) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.message = message;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-info.html',
                    controller: MBController
                });
                return instance.result;
            },
            question: function (head, question) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.question = question;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-question.html',
                    controller: MBController
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-info.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="message"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
            </div>'
        );
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-question.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="question"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
                <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            </div>'
        );
    }]);