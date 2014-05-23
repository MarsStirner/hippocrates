'use strict';

angular.module('WebMis20.services', []).
    factory('WMEvent', ['$http', '$q', 'WMEventService',
        function($http, $q, WMEventService) {
            var WMEvent = function(event_id, client_id) {
                this.event_id = parseInt(event_id);
                this.client_id = client_id;
                this.info = null;
                this.payment = null;
                this.diagnoses = [];
                this.services = [];
            };

            WMEvent.prototype.reload = function() {
                var self = this;
                var url = this.is_new() ? url_event_new : url_event_get;
                var params = this.is_new() ? { client_id: this.client_id } : { event_id: this.event_id }
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
                    services: this.services
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