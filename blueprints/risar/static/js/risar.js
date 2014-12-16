/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', ['$http', 'Config', '$q', function ($http, Config, $q) {
    var wrapper = function (method, url, params, data) {
        var defer = $q.defer();
        $http({
            method: method,
            url: url,
            params: params,
            data: data
        })
        .success(function (data) {
            defer.resolve(data.result)
        })
        .error(function (data, code) {
            defer.reject(data.meta)
        });
        return defer.promise;
    };
    this.schedule = function () {
        var date = arguments[0];
        var all = arguments[1];
        return wrapper('GET', Config.url.api_schedule, {
            date: (date)?(moment(date).format('YYYY-MM-DD')):undefined,
            all: all
        });
    };
    this.search_event = {
        get: function (query) {
            return wrapper('GET', Config.url.api_event_search, query)
        },
        lpu_list: function () {
            return wrapper('GET', Config.url.api_event_search_lpu_list)
        },
        lpu_doctors_list: function (org_id) {
            return wrapper('GET', Config.url.api_event_search_lpu_doctors_list, {
                org_id: org_id
            })
        }
    };
    this.chart = {
        get: function (event_id, ticket_id) {
            return wrapper('GET', Config.url.api_chart + ((event_id)?(event_id):''), {ticket_id: ticket_id});
        },
        delete: function (ticket_id) {
            return wrapper('DELETE', Config.url.api_chart_delete + ticket_id);
        }
    };
    this.attach_lpu = {
        save: function (client_id, data) {
            var url = '{0}'.format(Config.url.api_attach_lpu);
            return wrapper('POST', url, {client_id: client_id}, data);
        }
    };
    this.checkup = {
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_checkup_save.format(event_id), {}, data);
            }
    };
    this.anamnesis = {
        get: function (event_id) {
            var url = Config.url.api_anamnesis + event_id;
            return wrapper('GET', url);
        },
        mother: {
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_mother.format(event_id), {}, data);
            }
        },
        father: {
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_father.format(event_id), {}, data);
            }
        },
        pregnancies: {
            get: function (id) {
                return wrapper('GET', Config.url.api_anamnesis_pregnancies + id);
            },
            delete: function (id) {
                return wrapper('DELETE', Config.url.api_anamnesis_pregnancies + id);
            },
            undelete: function (id) {
                return wrapper('POST', Config.url.api_anamnesis_pregnancies + id + '/undelete');
            },
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_pregnancies + (data.id||''), {event_id: event_id}, data);
            }
        },
        transfusions: {
            get: function (id) {
                return wrapper('GET', Config.url.api_anamnesis_transfusions + id);
            },
            delete: function (id) {
                return wrapper('DELETE', Config.url.api_anamnesis_transfusions + id);
            },
            undelete: function (id) {
                return wrapper('POST', Config.url.api_anamnesis_transfusions + id + '/undelete');
            },
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_transfusions + (data.id||''), {event_id: event_id}, data);
            }
        },
        intolerances: {
            get: function (id, type) {
                var url = '{0}{1}/{2}'.format(Config.url.api_anamnesis_intolerances, type, id);
                return wrapper('GET', url);
            },
            delete: function (id, type) {
                var url = '{0}{1}/{2}'.format(Config.url.api_anamnesis_intolerances, type, id);
                return wrapper('DELETE', url);
            },
            undelete: function (id, type) {
                var url = '{0}{1}/{2}/undelete'.format(Config.url.api_anamnesis_intolerances, type, id);
                return wrapper('POST', url);
            },
            save: function (client_id, data) {
                var url = '{0}{1}/{2}'.format(Config.url.api_anamnesis_intolerances, data.type.code, (data.id||''));
                return wrapper('POST', url, {client_id: client_id}, data);
            }
        }
    };
}])
.filter('underlineNoVal', function () {
    return function(value, label) {
        if (value !== 0 && !value) {
            return '<span class="empty-value"></span> ' + (label || '');
        }
        return value + ' ' + (label || '');
    }
})
.service('RisarNotificationService', function () {
    var self = this;
    var recompilers = [];
    var indices = {};
    this.notifications = [];
    this.notify = function (code, message, severity) {
        var id = Math.floor(Math.random() * 65536);
        indices[id] = self.notifications.length;
        self.notifications.push({
            id: id,
            code: code,
            message: message,
            severity: severity
        });
        notify_recompilers();
        return id;
    };
    this.dismiss = function (id) {
        var index = indices[id];
        if (_.isNumber(index)) {
            self.notifications.splice(index, 1);
            notify_recompilers();
        } else {
            console.log('Tried dismissing missing message');
        }
    };
    this.register = function (recompile_function) {
        recompilers.push(recompile_function);
    };
    var notify_recompilers = function () {
        recompilers.forEach(function (recompile) {
            recompile(self.notifications);
        });
    }
})
.directive('alertNotify', function (RisarNotificationService, $compile) {
    return {
        restrict: 'AE',
        scope: true,
        link: function (scope, element, attributes) {
            var template =
                '<div class="alert alert-{0} abs-alert" role="alert">\
                    <button type="button" class="close" ng-click="$dismiss({2})">\
                        <span aria-hidden="true">&times;</span>\
                        <span class="sr-only">Close</span>\
                    </button>\
                    {1}\
                </div>';
            scope.$dismiss = function (id) {
                RisarNotificationService.dismiss(id);
            };
            var recompile = function (n) {
                var html = n.map(function (notification) {
                    return template.format(notification.severity || 'info', notification.message, notification.id)
                }).join('\n');
                var replace_element = $('<div>{0}</div>'.format(html));
                element.replaceWith(replace_element);
                $compile(replace_element)(scope);
                element = replace_element;
            };
            RisarNotificationService.register(recompile);
        }
    }
})
;