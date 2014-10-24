'use strict';

angular.module('WebMis20.services.models').
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
                        var contacts = data.result.client_data.contacts;
                        t.contacts = contacts !== null ? contacts : [];
                        var phones = data.result.client_data.phones;
                        t.phones = phones !== null ? phones : [];
                        var relations = data.result.client_data.relations;
                        t.relations = relations !== null ? relations : [];
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

            return WMClient;
        }
    ]);