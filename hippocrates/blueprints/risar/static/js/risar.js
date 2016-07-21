/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', [
        '$q', 'Config', 'NotificationService', '$window', 'ApiCalls',
        function ($q, Config, NotificationService, $window, ApiCalls) {
    var self = this;
    var wrapper = ApiCalls.wrapper;
    this.file_get = function (verb, url, data, target) {
        var form = document.createElement("form");
        form.action = url;
        form.method = verb;
        form.target = target || "_blank";
        if (data) {
            var json = angular.toJson(data);
            var input = document.createElement("textarea");
            input.name = 'json';
            input.value = json;
            form.appendChild(input);
        }
        form.style.display = 'none';
        document.body.appendChild(form);
        form.submit();
    };
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
    this.search_event = {
        get: function (query) {
            return wrapper('POST', Config.url.api_event_search, {}, query)
        },
        print: function (query) {
            self.file_get('POST', Config.url.api_event_print, query);
        },
        area_list: function () {
            return wrapper('GET', Config.url.api_event_search_area_list)
        },
        area_curator_list: function (areas) {
            return wrapper('POST', Config.url.api_event_search_area_curator_list, {}, {areas: areas})
        },
        curator_lpu_list: function (areas, curators) {
            return wrapper('POST', Config.url.api_event_search_curator_lpu_list, {}, {areas: areas, curators: curators})
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
    function Chart (urls) {
        var self = this;

        function on_event_created (ticket_id, event) {
            NotificationService.notify(
                200,
                [
                    'Пациентка поставлена на учёт: ',
                    {bold: true, text: event.person.name},
                    '. ',
                    {link: '#', text: 'Изменить'},
                    ' ',
                    {
                        click: function () {
                            self.delete(ticket_id).then(function success() {
                                $window.location.replace(urls.back);
                            })
                        },
                        text: 'Отменить'
                    }
                ],
                'success'
            );
        }
        function create (ticket_id, client_id) {
            return wrapper(
                'POST',
                urls.get,
                {ticket_id: ticket_id, client_id: client_id}
            ).then(function (event) {
                if (event.automagic) {
                    on_event_created(ticket_id, event);
                } else {
                    $window.location.replace(urls.html + '?event_id=' + event.id);
                }
                return event;
            })
        }

        this.get_header = function (event_id) {
            return wrapper('GET', urls.header + event_id);
        };
        this.delete = function (ticket_id) {
            return wrapper('DELETE', urls.delete + ticket_id);
        };
        this.close_event = function (event_id, data) {
            return wrapper('POST', urls.close.format(event_id), {}, data);
        };
        this.get = function (event_id, ticket_id, client_id) {
            if (event_id) {
                return wrapper('GET', urls.get + event_id)
            } else {
                var deferred = $q.defer();
                wrapper('GET', urls.get, {ticket_id: ticket_id, client_id: client_id}).then(
                    deferred.resolve,
                    function () {
                        create(ticket_id, client_id).then(
                            deferred.resolve,
                            deferred.reject
                        )
                    }
                );
                return deferred.promise;
            }
        };
        this._create = create;
    }
    this.chart = new Chart({
        get: Config.url.api_chart,
        header: Config.url.api_chart_header,
        delete: Config.url.api_chart_delete,
        close: Config.url.api_chart_close,
        html: Config.url.chart_pregnancy_html,
        back: Config.url.index_html
    });
    this.gynecologic_chart = new Chart({
        get: Config.url.gyn.chart,
        header: Config.url.gyn.header,
        delete: Config.url.gyn.delete,
        close: Config.url.gyn.close,
        html: Config.url.chart_pregnancy_html,
        back: Config.url.index_html
    });
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
    this.checkup_puerpera = {
        get_list: function (event_id) {
            return wrapper('GET', Config.url.api_checkup_puerpera_list + event_id);
        },
        get: function (checkup_id) {
            return wrapper('GET', Config.url.api_checkup_puerpera_get.format(checkup_id));
        },
        create: function (event_id, flat_code) {
            return wrapper('POST', Config.url.api_checkup_puerpera_new.format(event_id), undefined, {
                flat_code: flat_code
            });
        },
        save: function (event_id, data) {
            return wrapper('POST', Config.url.api_checkup_puerpera_save.format(event_id), {}, data);
        }
    };
    this.fetus = {
        get_fetus_list: function (event_id) {
            return wrapper('GET', Config.url.api_fetus_list + event_id);
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
        unpregnant: {
            get: function (event_id) {
                //todo: change url
                return wrapper('GET', Config.url.api_anamnesis_mother.format(event_id));
            },
            save: function (event_id, data) {
                //todo: change url
                return wrapper('POST', Config.url.api_anamnesis_mother.format(event_id), {}, data);
            }
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
        get_checkups: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_checkups + event_measure_id);
        },
        new_appointment: function (client_id, person_id, start_date) {
            this.child_window = $window.open(
                Config.url.url_schedule_appointment_html +
                    '?client_id=' + client_id +
                    '&person_id=' + person_id +
                    '&start_date=' + start_date,
                '_blank'
            );
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
        get_current_cards_overview: function (person_id, curation_level_code) {
            var url = Config.url.api_stats_current_cards_overview + person_id,
                args = {
                    curation_level_code: curation_level_code
                };
            return wrapper('GET', url, args);
        },
        get_pregnancy_week_diagram: function(person_id, curation_level_code) {
            var url = Config.url.api_stats_pregnancy_week_diagram + person_id,
                args = {
                    curation_level_code: curation_level_code
                };
            return wrapper('GET', url, args);
        },
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
        },
        get_card_fill_rates_overview_lpu: function (curator_id) {
            return wrapper('GET', Config.url.api_stats_card_fill_rates_lpu_overview + curator_id);
        },
        get_card_fill_rates_overview_doctor: function (curator_id, curation_level_code) {
            var url = Config.url.api_stats_card_fill_rates_doctor_overview + curator_id,
                args = {
                    curation_level_code: curation_level_code
                };
            return wrapper('GET', url, args);
        },
        get_risk_group_distribution: function (person_id, curation_level_code) {
            return wrapper('GET', Config.url.api_stats_risk_group_distribution + person_id, {curation_level_code: curation_level_code});
        },
        urgent_errands: function() {
            return wrapper('GET', Config.url.api_stats_urgent_errands)
        }
    };
    this.card_fill_rate = {
        get_chart: function (event_id) {
            return wrapper('GET', Config.url.api_chart_card_fill_history + event_id)
        }
    };
    this.risk_groups = {
        list: function (event_id) {
            return wrapper('GET', Config.url.api_chart_risk_groups_list.format(event_id))
        }
    };
    this.concilium = {
        get_list: function (event_id) {
            return wrapper('GET', Config.url.api_concilium_list_get.format(event_id))
        },
        get: function (event_id, concilium_id) {
            return wrapper('GET', Config.url.api_concilium_get.format(event_id) + concilium_id);
        }
    };
    this.utils = {
        get_person_contacts: function(person_id){
            return wrapper('GET', Config.url.api_person_contacts_get.format(person_id))
        }
    };
    this.errands = {
        get: function (errand_id) {
            return wrapper('GET', Config.url.api_errand_get + errand_id);
        },
        save: function (errand_id, data) {
            if (errand_id === undefined) {
                return wrapper('POST', Config.url.api_errand_save, {}, data)
                    .then(function (result) {
                        NotificationService.notify(undefined, 'Поручение успешно создано', 'success', 5000);
                        return result;
                    }, function (result) {
                        NotificationService.notify(undefined, 'Не удалось создать поручение', 'danger', 5000);
                        return $q.reject(result);
                    });
            } else {
                return wrapper('POST', Config.url.api_errand_save + errand_id, {}, data);
            }
        },
        del: function (errand) {
            return wrapper('DELETE', Config.url.api_errand_delete.format(errand.id), {}, errand)
        },
        list: function (args, data) {
            return wrapper('POST', Config.url.api_errands_get, args, data);
        },
        mark_as_read: function (errand) {
            return wrapper('POST', Config.url.api_errand_mark_as_read.format(errand.id), {}, errand)
        },
        execute: function (errand) {
            return wrapper('POST', Config.url.api_errand_execute.format(errand.id), {}, errand)
        }
    };
}])
.service('UserErrand', [
        'Simargl', 'RisarApi', 'ApiCalls', 'Config', 'OneWayEvent',
        function (Simargl, RisarApi, ApiCalls, Config, OneWayEvent) {
    var event_source = new OneWayEvent();
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

    Simargl.subscribe('errand:notify', function (msg) {
        get_errands_summary();
    });

    this.subscribe = event_source.eventSource.subscribe;

    this.mark_as_read = function (errand) {
        errand.reading_date =  new Date();
        return RisarApi.errands.mark_as_read(errand).then(get_errands_summary);
    };
    this.execute = function (errand) {
        errand.exec_date =  new Date();
        return RisarApi.errands.execute(errand).then(get_errands_summary);
    };
    this.delete_errand = function (errand) {
        return RisarApi.errands.del(errand).then(get_errands_summary);
    };
    this.create_errand = function (errand) {
        return RisarApi.errands.save(undefined, errand).then(get_errands_summary);
    };
    this.edit_errand = function (errand) {
        return RisarApi.errands.save(errand.id, errand).then(get_errands_summary);
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
.filter('collapse_diagnoses', [function () {
    return function (diag_list, kind) {
        var types = arguments[2];
        if (_.isUndefined(types)) {
            return _.filter(diag_list, function (diagnosis) {
                return _.any(diagnosis.diagnosis_types, function (value, key) {
                    return value.code == kind;
                });
            })
        } else {
            return _.filter(diag_list, function (diagnosis) {
                return _.any(diagnosis.diagnosis_types, function (value, key) {
                    return value.code == kind && [].has.apply(types, [key]);
                });
            })
        }
    }
}])
.service('ErrandModalService', ['$modal', 'RisarApi', function ($modal, RisarApi) {
    return {
        openNew: function (errand, is_author) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/errand.html',
                controller: ErrandModalCtrl,
                size: 'lg',
                resolve: {
                    model: function () {
                        return errand
                    },
                    is_author: function () {
                        return is_author;
                    }
                }
            });
            return instance.result;
        },
        openEdit: function (errand, is_author) {
            return RisarApi.errands.get(errand.id)
                .then(function (errand) {
                    var instance = $modal.open({
                    templateUrl: '/WebMis20/RISAR/modal/errand.html',
                    controller: ErrandModalCtrl,
                    size: 'lg',
                    resolve: {
                        model: function () {
                            return errand
                        },
                        is_author: function () {
                            return is_author;
                        }
                    }
                });
                return instance.result;
            });
        }
    }
}])
;