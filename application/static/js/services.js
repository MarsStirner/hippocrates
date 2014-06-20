'use strict';

angular.module('WebMis20.services', []).
    factory('WMClient', ['$http', '$q', '$rootScope',
        function($http, $q, $rootScope) {
            var WMClient = function(client_id) {
                this.client_id = client_id;
                this.changes = {}; // deleted items to save
            };

            WMClient.prototype.reload = function() {
                var t = this;
                var deferred = $q.defer();
                $http.get(url_client_get, {
                    params: {
                        client_id: this.client_id
                    }
                }).success(function(data) {
                    t.info = data.result.client_data.client;
                    var id_doc = data.result.client_data.id_document;
                    t.id_docs = id_doc !== null ? [id_doc] : [];
                    t.reg_address = data.result.client_data.reg_address;
                    t.live_addr = data.result.client_data.live_addr;
                    var cpol = data.result.client_data.compulsory_policy;
                    t.compulsory_policies = cpol !== null ? [cpol] : [];
                    t.voluntary_policies = data.result.client_data.voluntary_policies;
                    t.soc_statuses = data.result.client_data.soc_statuses;
                    t.invalidities = t.soc_statuses.filter(function(status){
                        return status.ss_class.code == 2;
                    });
                    t.works = t.soc_statuses.filter(function(status){
                        return status.ss_class.code == 3;
                    });
                    t.nationalities = t.soc_statuses.filter(function(status){
                        return status.ss_class.code == 4;
                    });

//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;
//                    t.id_doc = data.result.client_data.id_document;

                    t.appointments = data.result.appointments;
                    t.events = data.result.events;
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
//                    throw 'Error requesting Client, id = ' + t.client_id;
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
                    error(function(httpResponse) {
                        var message = httpResponse.result.name;
                        deferred.reject(message);
                    });
                return deferred.promise;
            };

            WMClient.prototype.get_changed_data = function() {
                var data = {
                    client_id: this.client_id
                };
                if (this.info.dirty) { data.info = this.info; }

                var changed_id_docs = this.id_docs.filter(function(el) {
                    return el.dirty;
                }).concat(this.changes.id_docs || []);
                data.id_docs = changed_id_docs.length ? changed_id_docs : undefined;

                var changed_cpolicies = this.compulsory_policies.filter(function(el) {
                    return el.dirty;
                }).concat(this.changes.compulsory_policies || []);
                data.compulsory_policies = changed_cpolicies.length ? changed_cpolicies : undefined;

                var changed_vpolicies = this.voluntary_policies.filter(function(el) {
                    return el.dirty;
                }).concat(this.changes.voluntary_policies || []);
                data.voluntary_policies = changed_vpolicies.length ? changed_vpolicies : undefined;

                var soc_statuses = this.invalidities.concat(this.works).concat(this.nationalities);
                var changed_soc_statuses = soc_statuses.filter(function(el) {
                    return el.dirty;
                }).concat(this.changes.invalidities || []).concat(this.changes.works || []).concat(this.changes.nationalities || []);
                data.soc_statuses = changed_soc_statuses.length ? changed_soc_statuses : undefined;

                return data;
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

            WMClient.prototype.add_allergy = function() {
                this.client_info['allergies'].push({
                    'nameSubstance': '',
                    'power': 0,
                    'createDate': '',
                    'deleted':0,
                    'notes': '' });
            };

            WMClient.prototype.add_medicament = function() {
                this.client_info['intolerances'].push({
                    'nameMedicament': '',
                    'power': 0,
                    'createDate': '',
                    'deleted':0,
                    'notes': '' });
            };

            WMClient.prototype.add_identification = function() {
                this.client_info['identifications'].push({
                    'deleted': 0,
                    'identifier': '',
                    'accountingSystem_code': '',
                    'checkDate': ''});
            };

            WMClient.prototype.add_contact = function() {
                this.client_info['contacts'].push({
                    'deleted': 0,
                    'contactType_code': '',
                    'contact': '',
                    'notes': ''});
            };

            WMClient.prototype.add_blood = function () {
                this.client_info['bloodHistory'].push({'bloodGroup_code': '',
                    'bloodDate': '',
                    'person_id': 0
                });
            };

            WMClient.prototype.add_relation = function (entity) {
                this.client_info[entity].push({'deleted': 0,
                    'relativeType_name': '',
                    'relativeType_code': '',
                    'other_id': 0
                });
            };

            WMClient.prototype.add_soc_status = function (class_name, class_code) {
                this[class_name].push({'deleted': 0,
                    'ss_class': {'code':class_code},
                    'ss_type': null,
                    'beg_date': null,
                    'end_date': null,
                    'self_document': {
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
                });
            };

            WMClient.prototype.delete_record = function(entity, record, deleted) {
                if (arguments.length < 3) {
                    deleted = 1;
                }
                if (record.id) {
                    record.deleted = deleted;
                    this.changes[entity] = record;
                } else {
                    var idx = this[entity].indexOf(record);
                    this[entity].splice(idx, 1);
                }
            };

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
            };

            return WMEventService;
        }
    ]);