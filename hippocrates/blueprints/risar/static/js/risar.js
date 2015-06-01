/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', [
    'Config', 'NotificationService', '$window', 'ApiCalls',
    function (Config, NotificationService, $window, ApiCalls) {
    var self = this;
    var wrapper = ApiCalls.wrapper;
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
        area_list: function () {
            return wrapper('GET', Config.url.api_event_search_area_list)
        },
        area_lpu_list: function (areas) {
            return wrapper('POST', Config.url.api_event_search_area_lpu_list, {}, {areas: areas})
        },
        lpu_doctors_list: function (org_id) {
            return wrapper('GET', Config.url.api_event_search_lpu_doctors_list, {
                org_id: org_id
            })
        }
    };
    this.search_event_ambulance = {
        get: function (query) {
            return wrapper('POST', Config.url.api_event_search_ambulance, {}, query)
        }
    };
    this.current_stats = {
        get: function () {
            return wrapper('GET', Config.url.api_current_stats);
        }
    };
    this.death_stats = {
        get: function () {
            return wrapper('GET', Config.url.api_death_stats);
        }
    };
    this.pregnancy_final_stats = {
        get: function () {
            return wrapper('GET', Config.url.api_pregnancy_final_stats);
        }
    };
    this.chart = {
        get: function (event_id, ticket_id) {
            return wrapper('GET', Config.url.api_chart + ((event_id)?(event_id):''), {ticket_id: ticket_id})
                .then(function (event_info) {
                    var chart = event_info.event,
                        automagic = event_info.automagic;
                    if (automagic) {
                        NotificationService.notify(
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
        },
        save_diagnoses: function(event_id, data){
            return wrapper('POST', Config.url.api_diagnoses_save.format(event_id), {}, data);
        }
    };
    this.event_routing = {
        get_destinations: function (diagnoses, client_id) {
            return wrapper('POST', Config.url.api_event_routing, {}, {
                diagnoses: diagnoses,
                client_id: client_id
            })
        },
        get_chart: function(event_id) {
            return wrapper('GET', Config.url.api_mini_chart + event_id)
        },
        attach_client: function (client_id, attachments) {
            return wrapper('POST', Config.url.api_attach_lpu_mini.format(client_id), {}, attachments)
                .then(function (changed) {
                    if (changed) {
                        NotificationService.notify(200, 'ЛПУ направления изменено', 'success')
                    } else {
                        NotificationService.notify(200, 'ЛПУ направления оставлено без изменений', 'info')
                    }

                })
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
    this.measure = {
        regenerate: function(action_id) {
            return wrapper('GET', Config.url.api_measure_generate + action_id)
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
.directive('riskRateIcon', function () {
    return {
        restrict: 'A',
        template: '<span ng-class="icon_class(riskRateIcon.id)" tooltip="[[tooltip(riskRateIcon.id)]]"></span>',
        scope: {
            riskRateIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 1) return 'ri-prenatal-risk text-success';
                if (rate == 2) return 'ri-prenatal-risk text-warning';
                if (rate == 3) return 'ri-prenatal-risk text-danger';
                return 'ri-prenatal-risk-undefined';
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
.directive('preeclampsiaRiskIcon', function () {
    return {
        restrict: 'A',
        template: '<span style="font-size: 32px" ng-class="icon_class(preeclampsiaRiskIcon.id)" tooltip="[[tooltip(preeclampsiaRiskIcon.id)]]"></span>',
        scope: {
            preeclampsiaRiskIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 1) return 'fa fa-exclamation-circle text-danger';
                if (rate == 2) return 'fa fa-exclamation-circle text-success';
                return 'fa fa-question';
            };
            scope.tooltip = function (rate) {
                if (rate == 1) return 'Пациентка входит в группу риска развития преэклампсии';
                if (rate == 2) return 'Пациентка НЕ входит в группу риска развития преэклампсии';
                return 'Риск развития преэклампсии ещё не выявлен';

            }
        }
    }
})
.directive('pregnancyWeekIcon', ['$filter', function ($filter) {
    return {
        restrict: 'A',
        template: '<span ng-class="icon_class(pregnancyWeekIcon)"' +
                  'tooltip="[[tooltip(pregnancyStartDate)]]"></span>',
        scope: {
            pregnancyWeekIcon: '=',
            pregnancyStartDate: '='
        },
        link: function (scope) {
            scope.icon_class = function (week) {
                if (1 <= week && week <= 40) {
                    return 'ri-pregnancy-week-' + week;
                } else if (week > 40) {
                    return 'ri-pregnancy-week-40h';
                } else {
                    return 'ri-pregnancy-week-undefined';
                }
            };
            scope.tooltip = function (psdate) {
                return 'Срок беременности (дата начала случая: {0})'.format(
                    $filter('asDate')(psdate) || 'не определена'
                );
            };
        }
    }
}])
;