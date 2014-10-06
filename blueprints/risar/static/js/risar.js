/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', ['$http', 'Config', '$q', function ($http, Config, $q) {
    this.schedule = function () {
        var date = arguments[0];
        var all = arguments[1];
        var defer = $q.defer();
        $http.get(Config.url.api_schedule, {
            params: {
                date: (date)?(moment(date).format('YYYY-MM-DD')):undefined,
                all: all
            }
        }).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    };
    this.chart = function () {
        var event_id = arguments[0];
        var ticket_id = arguments[1];
        var defer = $q.defer();
        var url = Config.url.api_chart;
        url += (event_id)?(event_id):'';
        $http.get(url, {
            params: {
                ticket_id: ticket_id
            }
        }).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    };
    this.chart_delete = function (ticket_id) {
        var defer = $q.defer();
        var url = Config.url.api_chart_delete + ticket_id;
        $http.delete(url).success(function (data, status) {
            if (status == 200) {
                defer.resolve(data.result)
            } else {
                defer.reject(data.meta)
            }
        });
        return defer.promise;
    };
    this.anamnesis = function (event_id) {
        var defer = $q.defer();
        var url = Config.url.api_anamnesis + event_id;
        $http.get(url).success(function (data) {
            if (data.meta.code != 200) {
                defer.reject(data.meta)
            } else {
                defer.resolve(data.result);
            }
        });
        return defer.promise;
    }
}])
.filter('underlineNoVal', function () {
    return function(value, label) {
        if (value !== 0 && !value) {
            return '<span class="empty-value"></span> ' + (label || '');
        }
        return value + ' ' + (label || '');
    }
})
.service('RisarNotificationService', function ($rootScope, $timeout) {
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