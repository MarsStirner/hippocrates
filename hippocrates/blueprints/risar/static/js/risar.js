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
    this.need_hospitalization = {
        get: function(){
            return wrapper('GET', Config.url.api_need_hospitalization)
        }
    };
    this.pregnancy_week_diagram  = {
        get: function(curation_level){
            return wrapper('GET', Config.url.api_pregnancy_week_diagram, {
                curation_level: curation_level
            });
        }
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
        lpu_doctors_list: function (orgs) {
            return wrapper('POST', Config.url.api_event_search_lpu_doctors_list, {}, {orgs: orgs})
        }
    };
    this.search_event_ambulance = {
        get: function (query) {
            return wrapper('POST', Config.url.api_event_search_ambulance, {}, query)
        }
    };
    this.current_stats = {
        get: function (curation_level) {
            return wrapper('GET', Config.url.api_current_stats, {
                curation_level: curation_level
            });
        }
    };
    this.urgent_errands = {
        get: function(){
            return wrapper('GET', Config.url.api_stats_urgent_errands)
        }
    };
    this.recent_charts = {
        get: function (data) {
            return wrapper('GET', Config.url.api_recent_charts, data);
        }
    };
    this.recently_modified_charts = {
        get: function (data) {
            return wrapper('POST', Config.url.api_recently_modified_charts, {}, data);
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
        get_header: function (event_id) {
            return wrapper('GET', Config.url.api_chart_header + event_id);
        },
        get: function (event_id, ticket_id, client_id) {
            return wrapper('GET', Config.url.api_chart + ((event_id)?(event_id):''), {
                ticket_id: ticket_id,
                client_id: client_id
            }).then(function (event_info) {
                var chart = event_info.event,
                    automagic = event_info.automagic;
                if (client_id) {
                    $window.location.replace(Config.url.chart_html + '?event_id=' + chart.id);
                    return chart;
                }
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
                return chart;
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
        get_list: function (event_id) {
            return wrapper('GET', Config.url.api_checkup_list + event_id);
        },
        get: function (checkup_id) {
            return wrapper('GET', Config.url.api_checkup_get.format(checkup_id));
        },
        create: function (event_id, flat_code) {
            return wrapper('POST', Config.url.api_checkup_new.format(event_id), undefined, {
                flat_code: flat_code
            });
        },
        save: function (event_id, data) {
            return wrapper('POST', Config.url.api_checkup_save.format(event_id), {}, data);
        }
    };
    this.gravidograma = {
        get: function (event_id){
            return wrapper('GET', Config.url.api_gravidograma + event_id);
        }
    };
    this.anamnesis = {
        get: function (event_id) {
            var url = Config.url.api_anamnesis.format(event_id);
            return wrapper('GET', url);
        },
        mother: {
            get: function (event_id) {
                return wrapper('GET', Config.url.api_anamnesis_mother.format(event_id));
            },
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_mother.format(event_id), {}, data);
            }
        },
        father: {
            get: function (event_id) {
                return wrapper('GET', Config.url.api_anamnesis_father.format(event_id));
            },
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
        get: function (event_id) {
            return wrapper('GET', Config.url.api_epicrisis.format(event_id));
        },
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
        get_chart: function (event_id) {
            return wrapper('GET', Config.url.api_chart_measure_list + event_id)
        },
        get_by_event: function (event_id, query) {
            return wrapper('POST', Config.url.api_measure_list + event_id, undefined, query)
        },
        regenerate: function (action_id) {
            return wrapper('GET', Config.url.api_event_measure_generate + action_id)
        },
        get: function (event_measure_id) {
            return wrapper('GET', Config.url.api_event_measure_get + event_measure_id);
        },
        remove: function (action_id) {
            return wrapper('POST', Config.url.api_event_measure_remove + action_id)
        },
        execute: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_execute + event_measure_id);
        },
        cancel: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_cancel + event_measure_id);
        },
        get_appointment: function (event_measure_id, appointment_id) {
            var url = Config.url.api_event_measure_appointment_get.format(event_measure_id);
            if (appointment_id) {
                url += appointment_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url);
        },
        save_appointment: function (event_measure_id, appointment_id, data) {
            var url = Config.url.api_event_measure_appointment_save.format(event_measure_id),
                method;
            if (appointment_id) {
                url += appointment_id;
                method = 'POST';
            } else {
                method = 'PUT';
            }
            return wrapper(method, url, {}, data)
                .then(function (action) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return action;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return result;
                });
        },
        get_em_result: function (event_measure_id, em_result_id) {
            var url = Config.url.api_event_measure_result_get.format(event_measure_id);
            if (em_result_id) {
                url += em_result_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url);
        },
        save_em_result: function (event_measure_id, em_result_id, data) {
            var url = Config.url.api_event_measure_result_save.format(event_measure_id),
                method;
            if (em_result_id) {
                url += em_result_id;
                method = 'POST';
            } else {
                method = 'PUT';
            }
            return wrapper(method, url, {}, data)
                .then(function (action) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return action;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return result;
                });
        }
    };
    this.stats = {
        get_obcl_info: function () {
            return wrapper('GET', Config.url.api_stats_obcl_get);
        },
        get_obcl_org_info: function (org_birth_care_id) {
            return wrapper('GET', Config.url.api_stats_obcl_orgs_get.formatNonEmpty(org_birth_care_id));
        },
        get_org_curation_info: function () {
            return wrapper('GET', Config.url.api_stats_org_curation_get);
        },
        get_perinatal_risk_info: function (curation_level) {
            return wrapper('GET', Config.url.api_stats_perinatal_risk_rate, {
                curation_level: curation_level
            });
        },
        get_pregnancy_pathology_info: function (curation_level_code) {
            return wrapper('GET', Config.url.api_stats_pregnancy_pathology, {
                curation_level_code: curation_level_code
            });
        },
        get_doctor_card_fill_rates: function (doctor_id) {
            return wrapper('GET', Config.url.api_stats_doctor_card_fill_rates + doctor_id);
        }
    };
    this.card_fill_rate = {
        get_chart: function (event_id) {
            return wrapper('GET', Config.url.api_chart_card_fill_history + event_id)
        }
    }
}])
.service('UserErrand', function (Simargl, ApiCalls, Config, OneWayEvent, CurrentUser, NotificationService) {
    var event_source = new OneWayEvent(),
        get_errands_url = Config.url.api_errands;
    if (!get_errands_url) {
        throw 'ВСЁ ПРОПАЛО!'
    }
    function get_errands_summary (pass) {
        ApiCalls.wrapper('GET', Config.url.api_errands_summary).then(_.partial(event_source.send, 'unread'));
        return pass;
    }
    Simargl.when_ready(function () {
        get_errands_summary();
        event_source.send('ready');
    });
    Simargl.subscribe('errand', function (msg) {
        get_errands_summary();
        event_source.send('new:id', msg.data.id);
    });
    this.subscribe = event_source.eventSource.subscribe;

    this.edit_errand = function (errand, exec) {
        var current_date = new Date();
        errand.exec = exec;
        if (errand.is_author){
            errand.reading_date = null;
        } else if (!errand.reading_date){
            errand.reading_date =  current_date;
        }
        return ApiCalls.wrapper('POST', Config.url.api_errand_edit.format(errand.id), {}, errand).then(get_errands_summary);
    };
    this.mark_as_read = function (errand){
        errand.reading_date =  new Date();
        return ApiCalls.wrapper('POST', Config.url.api_errand_mark_as_read.format(errand.id), {}, errand).then(get_errands_summary);
    };
    this.delete_errand = function (errand) {
        errand.deleted = 1;
        return ApiCalls.wrapper('POST', Config.url.api_errand_edit.format(errand.id), {}, errand).then(get_errands_summary);
    };
    this.get_errands = function (per_page, page, filters) {
        return ApiCalls.wrapper('POST', get_errands_url, {
            per_page: per_page,
            page: page
        }, filters)
    };
    this.create_errand = function (recipient, text, event_id, status, planned_exec_date) {
        Simargl.send_msg({
            topic: 'errand:new',
            recipient: recipient.id,
            sender: CurrentUser.id,
            data: { text: text, event_id: event_id, status: status, planned_exec_date:planned_exec_date},
            ctrl: true
        }).then(function (result) {
            NotificationService.notify(undefined, 'Поручение успешно создано', 'success', 5000);
            return result;
        }, function (result) {
            NotificationService.notify(undefined, 'Не удалось создать поручение', 'danger', 5000);
            return result;
        })
    };
})
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
                if (rate == 2) return 'ri-prenatal-risk text-green';
                if (rate == 3) return 'ri-prenatal-risk text-yellow';
                if (rate == 4) return 'ri-prenatal-risk text-red';
                if (rate == 1) return 'ri-prenatal-risk-undefined text-darkgray';
            };
            scope.tooltip = function (rate) {
                if (rate == 2) return 'У пациентки выявлена низкая степень риска';
                if (rate == 3) return 'У пациентки выявлена средняя степень риска';
                if (rate == 4) return 'У пациентки выявлена высокая степень риска';
                if (rate == 1) return 'У пациентки не выявлена степень риска';

            }
        }
    }
})
.directive('preeclampsiaRiskIcon', function () {
    return {
        restrict: 'A',
        template: '<span style="font-size: 120%" ng-class="icon_class(preeclampsiaRiskIcon.id)" tooltip="[[tooltip(preeclampsiaRiskIcon.id)]]"></span>',
        scope: {
            preeclampsiaRiskIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 1) return 'fa fa-exclamation-circle text-red';
                if (rate == 2) return 'fa fa-exclamation-circle text-green';
                return 'fa fa-question text-darkgray';
            };
            scope.tooltip = function (rate) {
                if (rate == 1) return 'Пациентка входит в группу риска развития преэклампсии';
                if (rate == 2) return 'Пациентка НЕ входит в группу риска развития преэклампсии';
                return 'Риск развития преэклампсии ещё не выявлен';

            }
        }
    }
})
.directive('preeclampsiaSuspIcon', function () {
    return {
        restrict: 'A',
        template: '<span style="font-size: 110%" ng-class="icon_class(preeclampsiaSuspIcon.code)" tooltip="[[tooltip(preeclampsiaSuspIcon.code)]]"></span>',
        scope: {
            preeclampsiaSuspIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 'mild') return 'fa fa-exclamation-triangle text-yellow';
                if (rate == 'heavy') return 'fa fa-exclamation-triangle text-red';
                if (rate == 'ChAH') return 'fa fa-exclamation-triangle';
                return 'fa fa-exclamation-triangle text-darkgray';
            };
            scope.tooltip = function (rate) {
                if (rate == 'mild') return 'Внимание! Симптомы пациентки указывают на преэклампсию умеренную';
                if (rate == 'heavy') return 'Внимание! Симптомы пациентки указывают на преэклампсию тяжелую';
                if (rate == 'ChAH') return 'Внимание! Симптомы пациентки указывают на преэклампсию на фоне ХАГ';
                return 'Симптомы преэклампсии не обнаружены';

            }
        }
    }
})
.directive('preeclampsiaConfirmedIcon', function () {
    return {
        restrict: 'A',
        template: '<span style="font-size: 110%" ng-class="icon_class(preeclampsiaConfirmedIcon.code)" tooltip="[[tooltip(preeclampsiaConfirmedIcon)]]"></span>',
        scope: {
            preeclampsiaConfirmedIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (rate) {
                if (rate == 'mild') return 'fa fa-exclamation-triangle text-yellow';
                if (rate == 'heavy') return 'fa fa-exclamation-triangle text-red';
                if (rate == 'ChAH') return 'fa fa-exclamation-triangle';
                return 'fa fa-exclamation-triangle text-darkgray';
            };
            scope.tooltip = function (rate) {
                if (!rate) return '';
                if (rate.code === 'unknown') return 'Диагноз преэклампсии не подтверждён';
                return 'Внимание! Установлен диагноз: преэклампсия ' + rate.name;
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
                    return 'ri-pregnancy-week-undefined text-darkgray';
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
.directive('measureTypeIcon', function () {
    return {
        restrict: 'A',
        template: '<span ng-class="icon_class(measureTypeIcon.code)" tooltip="[[measureTypeIcon.name]]"></span>',
        scope: {
            measureTypeIcon: '='
        },
        link: function (scope) {
            scope.icon_class = function (code) {
                if (code === 'lab_test') return 'ri-mt-lab-test';
                if (code === 'func_test') return 'ri-mt-func-test';
                if (code === 'checkup') return 'ri-mt-checkup';
                return 'ri-mt-func-other';
            };
        }
    }
})
.directive('cardFillRateIcon', ['$window', 'Config', function ($window, Config) {
    return {
        restrict: 'A',
        template: '\
<span style="font-size: 120%" class="cursor-pointer" ng-class="icon_class()" tooltip="[[ get_tooltip() ]]"\
    ng-click="open()"></span>\
',
        scope: {
            cardFillRateIcon: '=',
            eventId: '='
        },
        link: function (scope, element, attrs) {
            scope.icon_class = function () {
                if (!scope.cardFillRateIcon) return;
                var cfr = scope.cardFillRateIcon.card_fill_rate;
                if (cfr.code === 'filled') return 'fa fa-check-circle text-green';
                if (cfr.code === 'not_filled') return 'fa fa-exclamation-circle text-red';
                return 'fa fa-question text-darkgray';
            };
            scope.get_tooltip = function () {
                if (!scope.cardFillRateIcon) return;
                var cfr = scope.cardFillRateIcon.card_fill_rate;
                if (cfr.code === 'filled') return 'Карта заполнена полностью';
                else if (cfr.code === 'not_filled') return 'Карта заполнена не полностью';
                return 'Нет информации о заполненности карты';

            };
            scope.open = function () {
                $window.open('{0}?event_id={1}'.format(Config.url.card_fill_history, scope.eventId), '_self');
            };
        }
    }
}])
;