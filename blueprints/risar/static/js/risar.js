/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', [
    '$http', 'Config', '$q', 'RisarNotificationService', '$window',
    function ($http, Config, $q, RisarNotificationService, $window) {
    var self = this;
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
            var text = (code === 500) ? 'Внутренняя ошибка сервера.<br/>{0}' : 'Ошибка.<br/>{0}';
            RisarNotificationService.notify(
                code,
                text.format(data.meta.name),
                'danger'
            );
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
            return wrapper('POST', Config.url.api_event_search, {}, query)
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
    this.current_stats = {
        get: function () {
            return wrapper('GET', Config.url.api_current_stats);
        }
    };
    this.chart = {
        get: function (event_id, ticket_id) {
            return wrapper('GET', Config.url.api_chart + ((event_id)?(event_id):''), {ticket_id: ticket_id})
                .then(function (event_info) {
                    var chart = event_info.event,
                        automagic = event_info.automagic;
                    if (automagic) {
                        RisarNotificationService.notify(
                            200,
                            [
                                'Пациентка поставлена на учёт: ',
                                {
                                    bold: true,
                                    text: chart.person.name
                                }, '. ',
                                {
                                    link: '#',
                                    text: 'Изменить'
                                }, ' ',
                                {
                                    click: function () {
                                        self.chart.delete(ticket_id).then(function success() {
                                            $window.location.replace(Config.url.index_html);
                                        })
                                    },
                                    text: 'Отменить'
                                }
                            ],
                            'success'
                        );
                    }
                    return event_info.event;
                });
        },
        delete: function (ticket_id) {
            return wrapper('DELETE', Config.url.api_chart_delete + ticket_id);
        },
        close_event: function (event_id, data) {
            return wrapper('POST', Config.url.api_chart_close.format(event_id), {}, data);
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
    this.epicrisis = {
        save: function (event_id, data) {
            return wrapper('POST', Config.url.api_epicrisis.format(event_id), {}, data);
        },

        newborn_inspections: {
            delete: function(id){
                return wrapper('DELETE', Config.url.api_newborn_inspection.format(id));
            },
            undelete: function (id) {
                return wrapper('POST', Config.url.api_newborn_inspection.format(id) + '/undelete');
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
        scope: {},
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
            function compile (arg) {
                if (_.isArray(arg)) {
                    return arg.map(compile).join('');
                } else if (typeof arg === 'string') {
                    return arg;
                } else if (typeof arg !== 'object') {
                    return '';
                }
                var wrapper = '{0}';
                if (arg.hasOwnProperty('bold') && arg.bold) {
                    wrapper = '<b>{0}</b>'.format(wrapper)
                }
                if (arg.hasOwnProperty('italic') && arg.bold) {
                    wrapper = '<i>{0}</i>'.format(wrapper)
                }
                if (arg.hasOwnProperty('underline') && arg.bold) {
                    wrapper = '<u>{0}</u>'.format(wrapper)
                }
                if (arg.hasOwnProperty('link')) {
                    wrapper = '<a href={0}>{1}</a>'.format(arg.link, wrapper);
                } else if (arg.hasOwnProperty('click')) {
                    do {
                        var uniq = _.random(0x100000000);
                    } while (scope.func_map.hasOwnProperty(uniq));
                    scope.func_map[uniq] = arg.click;
                    wrapper = '<a style="cursor:pointer" ng-click="func_map[{0}]()">{1}</a>'.format(String(uniq), wrapper)
                }
                if (arg.hasOwnProperty('text')) {
                    return wrapper.format(compile(arg.text));
                }
                return '';
            }
            function recompile (n) {
                scope.func_map = {};
                var html = n.map(function (notification) {
                    return template.format(
                        notification.severity || 'info',
                        compile(notification.message),
                        notification.id
                    )
                }).join('\n');
                var replace_element = $('<div>{0}</div>'.format(html));
                element.replaceWith(replace_element);
                $compile(replace_element)(scope);
                element = replace_element;
            }
            RisarNotificationService.register(recompile);
        }
    }
})
.directive('riskRateIcon', function () {
    return {
        restrict: 'A',
        template: '<span class="fa" ng-class="icon_class(riskRateIcon.id)" tooltip="[[tooltip(riskRateIcon.id)]]"></span>',
        scope: {
            riskRateIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 1) return 'fa-circle text-success';
                if (rate == 2) return 'fa-circle text-warning';
                if (rate == 3) return 'fa-circle text-danger';
                return 'fa-question';
            };
            scope.tooltip = function (rate) {
                if (rate == 1) return 'У пациентки выявлен низкий риск невынашивания';
                if (rate == 2) return 'У пациентки выявлен средний риск невынашивания';
                if (rate == 3) return 'Внимание! У пациентки выявлен высокий риск невынашивания';
                return 'У пациентки риск невынашивания не выявлен';

            }
        }
    }
})
;