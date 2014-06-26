'use strict';

angular.module('WebMis20.services', []).
    factory('WMClient', ['$http', '$q', '$rootScope',
        function($http, $q, $rootScope) {
            var WMClient = function(client_id) {
                this.client_id = client_id;
            };

            WMClient.prototype.reload = function() {
                var t = this;
                var deferred = $q.defer();
                $http.get(url_client_get, {
                    params: {
                        client_id: this.client_id
                    }
                }).success(function(data) {
                    t.info = data.result.client_data.info;
                    var id_doc = data.result.client_data.id_document;
                    t.id_docs = id_doc !== null ? [id_doc] : [];
                    var reg_addr = data.result.client_data.reg_address;
                    t.reg_addresses = reg_addr !== null ? [reg_addr] : [];
                    var live_addr = data.result.client_data.live_address;
                    t.live_addresses = live_addr !== null ? [live_addr] : [];
                    var cpol = data.result.client_data.compulsory_policy;
                    t.compulsory_policies = cpol !== null ? [cpol] : [];
                    t.voluntary_policies = data.result.client_data.voluntary_policies;
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
                    t.relations = data.result.client_data.relations;
                    t.document_history = data.result.client_data.document_history;

                    t.appointments = data.result.appointments;
                    t.events = data.result.events;
                    t.deleted_entities = {}; // deleted items to save
                    deferred.resolve();
    //              $rootScope.$broadcast('client_loaded');
                }).error(function(data, status) {
//                    $rootScope.$broadcast('load_error', {
//                        text: 'Ошибка при загрузке клиента ' + t.id,
//                        data: data,
//                        code: status,
//                        type: 'danger'
//                    });
                    var message = status === 404 ? 'Пациент с id ' + t.client_id + ' не найден.' : data.result;
                    deferred.reject(message);
                });
                return deferred.promise;
            };

            WMClient.prototype.get_events_appointments = function() {
                var t = this;
                var deferred = $q.defer();
                $http.get(url_client_events_appointments, {
                    params: {
                        client_id: this.client_id
                    }
                }).success(function(data) {
                    t.info = data.result.client_data.info;
                    var id_doc = data.result.client_data.id_document;
                    t.id_docs = id_doc !== null ? [id_doc] : [];
                    var cpol = data.result.client_data.compulsory_policy;
                    t.compulsory_policies = cpol !== null ? [cpol] : [];
                    t.voluntary_policies = data.result.client_data.voluntary_policies;

                    t.appointments = data.result.appointments;
                    t.events = data.result.events;
                    t.deleted_entities = {}; // deleted items to save
                    deferred.resolve();
    //              $rootScope.$broadcast('client_loaded');
                }).error(function(data, status) {
//                    $rootScope.$broadcast('load_error', {
//                        text: 'Ошибка при загрузке клиента ' + t.id,
//                        data: data,
//                        code: status,
//                        type: 'danger'
//                    });
                    var message = data.result;
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

            WMClient.prototype.add_address = function(type) {
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
                this[entity].push(obj);
                return obj;
            };

            WMClient.prototype.copy_address = function(addr, from_addr, same) {
                if (!from_addr.id && !from_addr.dirty) {
                    alert('Для копирования адреса заполните сначала адрес регистрации');
                    addr.same_as_reg = undefined;
                    return;
                }
                var cur_id = addr.id;
                if (cur_id) {
                    var msg = same ?
                        'При копировании адреса текущая запись адреса будет удалена и станет доступна\
                         для просмотра в истории. Продолжить?' :
                        'Текущий адрес будет удален. Продолжить?';
                    if (!confirm(msg)) {
                        addr.same_as_reg = !addr.same_as_reg;
                        return;
                    }
                }
                this.delete_record('live_addresses', addr, 2);
                addr = this.add_address(1);
                if (same) {
                    angular.copy(from_addr, addr);
                    addr.id = null;
                    addr.copy_from_id = from_addr.id;
                    addr.dirty = true;
                }
                addr.same_as_reg = same;
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
    factory('WMEvent', ['$http', '$q', 'WMEventService',
        function($http, $q, WMEventService) {
            var WMEvent = function(event_id, client_id, ticket_id) {
                this.event_id = parseInt(event_id);
                this.client_id = client_id;
                this.ticket_id = ticket_id;
                this.info = null;
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
                }).
                    success(function(data) {
                        self.info = data.result.event;
                        self.payment = data.result.payment || { payments: [] };
                        self.diagnoses = data.result.diagnoses || [];
                        self.services = data.result.services && data.result.services.map(function(service) {
                            return new WMEventService(service, self.payment.payments); //todo mb null
                        }) || [];
                        deferred.resolve();
                    }).
                    error(function(data) {
                        deferred.reject('error load event');
                    });
                return deferred.promise;
            };

            WMEvent.prototype.save = function() {
                var self = this;
                var deferred = $q.defer();
                $http.post(url_event_save, {
                    event: this.info,
                    payment: this.payment,
                    services: this.services,
                    ticket_id: this.ticket_id
                }).
                    success(function(data) {
                        deferred.resolve(data.result.id);
                    }).
                    error(function(data) {
                        deferred.reject('error save event');
                    });
                return deferred.promise;
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
    factory('WMEventService', [
        function() {
            var WMEventService = function(service_data, payments) {
                angular.extend(this, service_data);
                var self = this;
                this.payments = payments.filter(function(p) {
                    return p.service_id === self.service_id && self.actions.indexOf(p.action_id) != -1;
                });
                this.refresh();
            };

            WMEventService.prototype.refresh = function() {
                var self = this;
                var unpaid = this.actions.filter(function(a_id) {
                    return self.payments.filter(function(p) {
                        return p.action_id === a_id && p.service_id === self.service_id && (p.sum + p.sum_discount) === self.price;
                    }).length === 1 ? undefined : true;
                });

                this.fully_paid = this.amount === this.actions.length && unpaid.length === 0;
                this.partially_paid = unpaid.length > 0 && unpaid.length < this.actions.length;
                this.paid_count = this.actions.length - unpaid.length;
                this.coord_count = this.coord_actions.length;
            };

            return WMEventService;
        }
    ]);