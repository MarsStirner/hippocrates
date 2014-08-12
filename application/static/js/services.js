'use strict';

angular.module('WebMis20.services', []).
    factory('WMClient', ['$http', '$q', '$rootScope',
        function($http, $q, $rootScope) {
            var WMClient = function(client_id) {
                this.client_id = client_id;
            };

            WMClient.prototype.reload = function(info_type) {
                var t = this;
                var deferred = $q.defer();
                var url_args = { client_id: this.client_id };
                if (info_type !== undefined) { url_args[info_type] = true; }

                $http.get(url_client_get, {
                    params: url_args
                }).success(function(data) {
                    t.info = data.result.client_data.info;
                    var id_doc = data.result.client_data.id_document;
                    t.id_docs = id_doc !== null ? [id_doc] : [];
                    var cpol = data.result.client_data.compulsory_policy;
                    t.compulsory_policies = cpol !== null ? [cpol] : [];
                    t.voluntary_policies = data.result.client_data.voluntary_policies;

                    if (info_type === undefined || info_type == 'for_event') {
                        var reg_addr = data.result.client_data.reg_address;
                        t.reg_addresses = reg_addr !== null ? [reg_addr] : [];
                        var live_addr = data.result.client_data.live_address;
                        if (live_addr !== null && live_addr.synced) {
                            reg_addr.live_id = live_addr.id;
                            reg_addr.synced = true;
                            live_addr = reg_addr;
                        }
                        t.live_addresses = live_addr !== null ? [live_addr] : [];
                        var blood_types = data.result.client_data.blood_history;
                        t.blood_types = blood_types !== null ? blood_types : [];
                        var allergies = data.result.client_data.allergies;
                        t.allergies = allergies !== null ? allergies : [];
                        var intolerances = data.result.client_data.intolerances;
                        t.intolerances = intolerances !== null ? intolerances : [];
                        t.soc_statuses = data.result.client_data.soc_statuses;
                        t.invalidities = t.soc_statuses.filter(function(status) {
                            return status.ss_class.code == 2;
                        });
                        t.works = t.soc_statuses.filter(function(status) {
                            return status.ss_class.code == 3;
                        });
                        t.nationalities = t.soc_statuses.filter(function(status) {
                            return status.ss_class.code == 4;
                        });
                        t.contacts = data.result.client_data.contacts;
                        t.phones = data.result.client_data.phones;
                        t.relations = data.result.client_data.relations;
                        t.document_history = data.result.client_data.document_history;

                        t.deleted_entities = {}; // deleted items to save
                    } else if (info_type === 'for_servicing') {
                        t.appointments = data.result.appointments;
                        t.events = data.result.events;
                    }

                    deferred.resolve();
                }).error(function(data, status) {
                    var message = status === 404 ? 'Пациент с id ' + t.client_id + ' не найден.' : data.result;
                    deferred.reject(message);
                });
                return deferred.promise;
            };

            WMClient.prototype.save = function() {
                var data = this.get_changed_data();
                var t = this;
                var deferred = $q.defer();
                $http.post(url_client_save, data).
                    success(function(value, headers) {
                        deferred.resolve(value['result']);
                    }).
                    error(function(response) {
                        var rr = response.result;
                        var message = rr.name + ': ' + (rr.data ? rr.data.err_msg : '');
                        deferred.reject(message);
                    });
                return deferred.promise;
            };

            WMClient.prototype.get_changed_data = function() {
                var data = {
                    client_id: this.client_id
                };
                if (this.info.dirty) { data.info = this.info; }
                data.id_docs = this._get_entity_changes('id_docs');
                data.reg_addresses = this._get_entity_changes('reg_addresses');
                data.live_addresses = this._get_entity_changes('live_addresses');
                data.compulsory_policies = this._get_entity_changes('compulsory_policies');
                data.voluntary_policies = this._get_entity_changes('voluntary_policies');
                data.blood_types = this._get_entity_changes('blood_types');
                data.allergies = this._get_entity_changes('allergies');
                data.intolerances = this._get_entity_changes('intolerances');
                var soc_status_changes = [].
                    concat(this._get_entity_changes('invalidities') || []).
                    concat(this._get_entity_changes('works') || []).
                    concat(this._get_entity_changes('nationalities') || []);
                data.soc_statuses = soc_status_changes.length ? soc_status_changes : undefined;
                data.relations = this._get_entity_changes('relations');
                data.contacts = this._get_entity_changes('contacts');

                return data;
            };

            WMClient.prototype._get_entity_changes = function(entity) {
                var dirty_elements = this[entity].filter(function(el) {
                    return el.dirty;
                });
                var deleted_elements = this.deleted_entities[entity] || [];
                var changes = dirty_elements.concat(deleted_elements.filter(function(del_elmnt) {
                    return dirty_elements.indexOf(del_elmnt) === -1;
                }));
                return changes.length ? changes : undefined;
            };

            WMClient.prototype.is_new = function() {
                return this.client_id === 'new';
            };

            WMClient.prototype.add_id_doc = function() {
                this.id_docs.push({
                    "id": null,
                    "deleted": 0,
                    "doc_type": null,
                    "serial": null,
                    "number": null,
                    "beg_date": null,
                    "end_date": null,
                    "origin": null,
                    "doc_text": null
                });
            };

            WMClient.prototype.add_cpolicy = function() {
                this.compulsory_policies.push({
                    "id": null,
                    "deleted": 0,
                    "policy_type": null,
                    "serial": null,
                    "number": null,
                    "beg_date": null,
                    "end_date": null,
                    "insurer": null,
                    "policy_text": null
                });
            };

            WMClient.prototype.add_vpolicy = function() {
                this.voluntary_policies.push({
                    "id": null,
                    "deleted": 0,
                    "policy_type": null,
                    "serial": null,
                    "number": null,
                    "beg_date": null,
                    "end_date": null,
                    "insurer": null,
                    "policy_text": null
                });
            };

            WMClient.prototype.add_blood_type = function () {
                this.blood_types.unshift({
                    'id': null,
                    'blood_type': null,
                    'date': null,
                    'person': null
                });
            };

            WMClient.prototype.add_allergy = function() {
                this.allergies.push({
                    'id': null,
                    'deleted': 0,
                    'name': null,
                    'power': null,
                    'date': null,
                    'notes': null
                });
            };

            WMClient.prototype.add_med_intolerance = function() {
                this.intolerances.push({
                    'id': null,
                    'deleted': 0,
                    'name': null,
                    'power': null,
                    'date': null,
                    'notes': null
                });
            };

            WMClient.prototype.add_soc_status = function (class_name, class_code) {
                var document = null;
                if (class_code != 4) {
                    document = {
                        "id": null,
                        "deleted": 0,
                        "doc_type": null,
                        "serial": null,
                        "number": null,
                        "beg_date": null,
                        "end_date": null,
                        "origin": null,
                        "doc_text": null
                    }
                }
                this[class_name].push({'deleted': 0,
                    'ss_class': {'code':class_code},
                    'ss_type': null,
                    'beg_date': null,
                    'end_date': null,
                    'self_document': document
                });
            };

            WMClient.prototype.add_relation = function () {
                this.relations.push({
                    id: null,
                    deleted: 0,
                    rel_type: null,
                    direct: true,
                    relative: null
                });
            };

            WMClient.prototype.add_contact = function() {
                this.contacts.push({
                    'id': null,
                    deleted: 0,
                    contact_type: null,
                    contact_text: null,
                    notes: null
                });
            };

            WMClient.prototype.delete_record = function(entity, record, deleted) {
                if (arguments.length < 3) {
                    deleted = 1;
                }
                if (record.id) {
                    record.deleted = deleted;
                    angular.isArray(this.deleted_entities[entity]) ?
                        this.deleted_entities[entity].push(record) :
                        this.deleted_entities[entity] = [record];
                } else {
                    var idx = this[entity].indexOf(record);
                    this[entity].splice(idx, 1);
                }
            };

//            WMClient.prototype.add_identification = function() {
//                this.client_info['identifications'].push({
//                    'deleted': 0,
//                    'identifier': '',
//                    'accountingSystem_code': '',
//                    'checkDate': ''});
//            };
            return WMClient;
        }
    ]).
    service('WMClientController', [function () {
        function get_actual_address (client, entity) {
            var addrs =  client[entity].filter(function (el) {
                return el.deleted === 0;
            });
            return addrs.length === 1 ? addrs[0] : null;
        }

        function make_address_copy(address, type, copy_into) {
            var copy = copy_into !== undefined ? angular.copy(address, copy_into) : angular.copy(address);
            copy.type = type;
            copy.synced = false;
            copy.dirty = true;
            if (type === 1) {
                copy.id = copy.live_id;
            }
            copy.live_id = undefined;
            return copy;
        }

        function delete_existing_record(client, entity, record, deleted) {
            if (record.id) {
                record.deleted = deleted;
                angular.isArray(client.deleted_entities[entity]) ?
                    client.deleted_entities[entity].push(record) :
                    client.deleted_entities[entity] = [record];
            }
        }

        return {
            formatSnils: function (snils) {
                return snils && snils.length === 11 ?
                    [snils.substr(0, 3), '-',
                     snils.substr(3, 3), '-',
                     snils.substr(6, 3), ' ', snils.substr(9, 2)].join('') :
                    '';
            },
            push_address: function (client, type) {
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';
                var obj = {
                    "id": null,
                    "deleted": 0,
                    "type": type,
                    "address": null,
                    "free_input": null,
                    "locality_type": null,
                    "text_summary": null
                };
                client[entity].push(obj);
                return obj;
            },
            add_new_address: function (client, type) {
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';
                var cur_addr = get_actual_address(client, entity);
                if (cur_addr) {
                    var msg = [
                        'При добавлении нового адреса старый адрес будет удален',
                        cur_addr.id ? ' и станет доступен для просмотра в истории' : '',
                        '. Продолжить?'
                    ].join('');
                    if (confirm(msg)) {
                        this.delete_address(client, type, cur_addr, 2, true);
                        this.push_address(client, type);
                    }
                } else {
                    this.push_address(client, type);
                }
            },
            delete_address: function (client, type, addr, deleted, silent) {
                if (deleted === undefined) {
                    deleted = 1;
                }
                if (silent === undefined) {
                    silent = false;
                }
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';

                if (silent || confirm('Адрес будет удален. Продолжить?')) {
                    if (addr.synced) {
                        var addr_idx_to_delete = client[entity].indexOf(addr),
                            addr_to_delete = make_address_copy(addr, type),
                            live_addr,
                            new_live_addr,
                            reg_addr,
                            la_idx;

                        // delete what should be deleted
                        delete_existing_record(client, entity, addr_to_delete, deleted);
                        this.delete_record(client, entity, null, deleted, addr_idx_to_delete);
                        // and make synced address independent record
                        if (type === 0) {
                            live_addr = get_actual_address(client, 'live_addresses');
                            la_idx = client.live_addresses.indexOf(live_addr);
                            this.delete_record(client, 'live_addresses', null, deleted, la_idx);

                            new_live_addr = this.push_address(client, 1);
                            make_address_copy(live_addr, 1, new_live_addr);
                        } else if (type === 1) {
                            reg_addr = get_actual_address(client, 'reg_addresses');
                            reg_addr.synced = false;
                            reg_addr.live_id = undefined;
                        }
                    } else {
                        this.delete_record(client, entity, addr, deleted);
                    }
                }
            },
            sync_addresses: function (client, live_addr, same) {
                var reg_addr = get_actual_address(client, 'reg_addresses');
                if (!reg_addr ) {
                    alert('Для копирования адреса заполните сначала адрес регистрации');
                    live_addr.synced = undefined;
                    return;
                }
                var to_be_changed = live_addr.synced ? live_addr.live_id : live_addr.id;
                if (to_be_changed) {
                    var msg = (same ? 'При копировании адреса текущая ' : 'Текущая ') +
                        'запись адреса будет удалена и станет доступна для просмотра в истории. Продолжить?';
                    if (!confirm(msg)) {
                        live_addr.synced = !live_addr.synced;
                        return;
                    }
                }

                if (same) {
                    live_addr.synced = false; // was updated after checkbox toggle
                    this.delete_record(client, 'live_addresses', live_addr, 2);
                    reg_addr.synced = true;
                    reg_addr.live_id = null;
                    client.live_addresses.push(reg_addr);
                    reg_addr.dirty = true;
                } else {
                    var live_addr_idx = client.live_addresses.indexOf(live_addr),
                        live_addr_to_delete = make_address_copy(live_addr, 1);

                    // current live address record to be deleted
                    // if live address was stored before, place its copy record in list for deletion
                    delete_existing_record(client, 'live_addresses', live_addr_to_delete, 2);
                    // remove former synced live address record. Need to use index and null record
                    // lest reg address record would not be placed in deletion list
                    this.delete_record(client, 'live_addresses', null, 2, live_addr_idx);

                    // detach reg address
                    reg_addr.synced = false;
                    reg_addr.live_id = undefined;

                    // add new live address as copy from reg address
                    var new_live_addr = this.push_address(client, 1);
                    make_address_copy(reg_addr, 1, new_live_addr);
                    new_live_addr.id = null;
                }
            },
            add_new_invalidity: function(client) {
                var invld = client.invalidities.filter(function(i) {
                    return i.deleted === 0;
                });
                var cur_invld = invld[invld.length - 1];
                if (invld.length) {
                    var msg = [
                        'При добавлении новой инвалидности старая запись будет удалена',
                        cur_invld.id ? ' и станет доступна для просмотра в истории' : '',
                        '. Продолжить?'
                    ].join('');
                    if (confirm(msg)) {
                        client.delete_record('invalidities', cur_invld, 2);
                        client.add_soc_status('invalidities', 2);
                    }
                } else {
                    client.add_soc_status('invalidities', 2);
                }
            },
            delete_record: function(client, entity, record, deleted, idx) {
                if (arguments.length < 4) {
                    deleted = 1;
                }
                if (record && record.id) {
                    delete_existing_record(client, entity, record, deleted);
                } else {
                    var idx = idx !== undefined ? idx : client[entity].indexOf(record);
                    client[entity].splice(idx, 1);
                }
            }
        };
    }]).
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

                    self.diagnoses = data.result.diagnoses || [];

                    var p = data.result.payment;
                    self.payment = {
                        local_contract: p.local_contract ? p.local_contract : null,
                        payments: new WMEventPaymentList(p.payments)
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
                    payment: this.payment,
                    services: this.services,
                    ticket_id: this.ticket_id,
                    close_event: close_event
                }).
                    success(function(data) {
                        deferred.resolve(data.result.id);
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
                return final_diagnosis[0] ? final_diagnosis.length : null
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
    factory('WMEventServiceGroup', ['$rootScope', 'WMEventController',
        function($rootScope, WMEventController) {
            var WMSimpleAction = function (action, service_group) {
                if (!action) {
                    action = {
                        action_id: null,
                        account: null,
                        amount: 1,
                        beg_date: null,
                        end_date: null,
                        coord_date: null,
                        coord_person: null,
                        sum: service_group.price,
                        assigned: service_group.all_assigned,
                        planned_end_date: service_group.all_planned_end_date !== false ?
                            service_group.all_planned_end_date : null
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
                        assignable: [], // info list of assignable properties
                        all_assigned: [], // [] - all have same assignments, False - have different assignments
                        all_planned_end_date: null // date - all have same dates, False - have different dates
                    }
                }

                this.total_sum = undefined;
                this.account_all = undefined; // false - none, true - all, null - some
                this.coord_all = undefined;

                this.fully_paid = undefined;
                this.partially_paid = undefined;
                this.paid_count = undefined;

                this.coord_count = undefined;
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
                        if (act.account !== n) {
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
                        WMEventController.coordinate(act, !n)
                    });
                }, true);
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.coord_person ? act.coord_person.id : null;
                    });
                }, function (n, o) {
                    var total_count = n.length;
                    self.refresh_coord_info();
                    self.coord_all = (total_count === this.coord_count) ? true :
                        (this.coord_count === 0) ? false : null;
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
                            return ped === ref_ped;
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
                        return 1;
                    }
                    return 1;
                }).forEach(function (ch) {
                    ch.suffice = bank > ch.action.sum;
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
                var sg = event.services[sg_idx];
                var action_id_list = sg.actions.map(function (a) {
                    return a.action_id;
                });
                var group_saved = action_id_list.every(function (a_id) {
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
                var sg_idx = event.services.indexOf(sg),
                    action_idx = event.services[sg_idx].actions.indexOf(action);
                if (action.action_id) {
                    $http.post(
                        url_for_event_api_service_delete_service, {
                            action_id_list: [action.action_id]
                        }
                    ).success(function () {
                        sg.actions.splice(action_idx, 1);
                    }).error(function () {
                        alert('error');
                    });
                } else {
                    sg.actions.splice(action_idx, 1);
                }
            },
            coordinate: function (action, off) {
                var user = off ? null : {id: current_user_id},
                    date = off ? null : new Date();
                if ((action.is_coordinated() && off) || (!action.is_coordinated() && !off)) {
                    action.coord_person = user;
                    action.coord_date = date;
                }
            }
//            coordinate_service: function (event, service) {
//                service.coord_person = current_user_id;
//                service.coord_date = new Date();
//                if (!event.is_new()) {
//                    $http.post(
//                        url_for_event_api_service_add_coord, {
//                            event_id: event.info.id,
//                            finance_id: event.info.contract.finance.id,
//                            service: service
//                        }
//                    ).success(function(result) {
//                        service.actions = result['result']['data'];
//                        service.coord_actions = result['result']['data'];
//                        service.coord_count = service.coord_actions.length;
//                    }).error(function() {
//                        service.coord_person_id = undefined;
//                        alert('error');
//                    });
//                } else {
//                    service.coord_count = service.amount;
//                }
//            },
//            uncoordinate_service: function(event, service) {
//                if (event.info.id){
//                    $http.post(
//                        url_for_event_api_service_remove_coord, {
//                            action_id: service.coord_actions,
//                            coord_person_id: null
//                        }
//                    ).success(function() {
//                        service.coord_actions = [];
//                        service.coord_person_id = null;
//                        service.coord_count = service.coord_actions.length;
//                    }).error(function() {
//                        alert('error');
//                    });
//                } else {
//                    service.coord_actions = [];
//                    service.coord_person_id = null;
//                    service.coord_count = service.coord_actions.length;
//                }
//            }
        };
    }]);