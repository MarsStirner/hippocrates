/**
 * Created by mmalkov on 24.09.14.
 */
'use strict';

WebMis20
.service('RisarApi', [
        '$q', 'Config', 'NotificationService', '$window', 'ApiCalls', 'RisarEventControlService', 'WMConfig',
        function ($q, Config, NotificationService, $window, ApiCalls, RisarEventControlService, WMConfig) {
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
    this.print_jsp_epicrisis = function(data) {
        self.file_get('POST',  Config.url.print_jsp_epicrisis, data)
    };
    this.print_ticket_25 = function (action_id, fmt) {
        self.file_get('POST', Config.url.print_checkup_ticket_25, {action_id: action_id, extension: fmt})
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
            return wrapper('POST', Config.url.api_event_search, {}, query);
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
        },
        openExtendedSearch: function (args, external) {
            $window.open(Config.url.search_html + '?' + $.param(args), external ? '_blank' : '_self');
        },
        getExtendedSearchUrl: function (args) {
            return Config.url.search_html + '?' + $.param(args);
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
        self.urls = urls;

        self.create = function (ticket_id, client_id, gyn_event_id) {
            return wrapper(
                'POST',
                 self.urls.get.format(''),
                {ticket_id: ticket_id, client_id: client_id, gyn_event_id: gyn_event_id}
            ).then(function (event) {
                if (event.automagic) {
                    self.on_event_created(ticket_id, event);
                } else {
                    $window.location.replace( self.urls.html + '?event_id=' + event.id);
                }
                return event;
            })
        };
        this.take_control = function(event_id) {
          return wrapper('POST', Config.url.api_chart_control.format('take_control', event_id, ''));
        };
        this.remove_control = function(event_id) {
           return wrapper('POST', Config.url.api_chart_control.format('remove_control', event_id, ''));
        };
        this.transfer = function(event_id, to_person_id, data) {
           return wrapper('POST', Config.url.api_chart_transfer.format(event_id, to_person_id), {}, data);
        };
        this.update_set_date = function(event_id, data) {
           return wrapper('PUT', Config.url.api_update_set_date.format(event_id), {}, data);
        };
        this.get_header = function (event_id) {
            return wrapper('GET',  self.urls.header.format(event_id));
        };
        this.delete = function (ticket_id, event_id) {
            var formatted_ticket_id = ticket_id || '0',
                targetUrl = self.urls.delete.format(formatted_ticket_id);
            if (!ticket_id) {
                if ( event_id!== undefined ) {
                    targetUrl += '?event_id='+event_id
                }
            }
            return wrapper('DELETE', targetUrl);
        };
        self.on_event_created = function (ticket_id, event, data) {
            NotificationService.notify(
                200,
                [
                    'Пациентка поставлена на учёт: ',
                    {bold: true, text: event.person.name},
                    '. ',
                    {
                        click: function () {
                            RisarEventControlService.open_edit_modal(event,  self.urls)
                                .then(function () {
                                    $window.location.replace( self.urls.html + '?event_id=' + event.id);
                                })
                        },
                        text: 'Изменить'
                    },
                    ' ',
                    {
                        click: function () {
                            self.delete(ticket_id, event.id).then(function success() {
                                $window.location.replace( self.urls.back);
                            })
                        },
                        text: 'Отменить'
                    }
                ],
                'success'
            );
        };
        this.close_event = function (event_id, data, edit_callback, cancel_callback) {
            var show_notify = !data.cancel;
            return wrapper(
                'POST',  self.urls.close.format(event_id), {}, data
            ).then(function (data) {
                var close_notify = function() {
                    NotificationService.dismiss(notify_id);
                };
                if (show_notify) {
                    var notify_id = NotificationService.notify(
                        200,
                        [
                            'Карта закрыта. ',
                            {
                                click: function () {
                                    edit_callback(data).then(close_notify);
                                },
                                text: 'Изменить'
                            }, ' ',
                            {
                                click: function () {
                                    cancel_callback(data).then(close_notify);
                                },
                                text: 'Отменить'
                            }
                        ],
                        'success'
                    );
                }
            })
        };
        this.get = function (event_id, ticket_id, client_id, gyn_event_id) {
            if (event_id) {
                return wrapper('GET',  self.urls.get.format(event_id))
            } else {
                var deferred = $q.defer();
                wrapper('GET',  self.urls.get.format(''), {ticket_id: ticket_id, client_id: client_id}).then(
                    function (data) {
                        if (!data) {
                            self.create(ticket_id, client_id, gyn_event_id).then(
                                deferred.resolve,
                                deferred.reject
                            )
                        } else {
                            deferred.resolve(data);
                        }
                    },
                    deferred.reject
                );
                return deferred.promise;
            }
        };
        this._create = self.create;
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
        html: Config.url.chart_gynecological_html,
        back: Config.url.index_html
    });
    this.gynecologic_chart.on_event_created = function (ticket_id, event) {
            var self = this;
            NotificationService.notify(
                200,
                [
                    'Карта создана. ',
                    {
                        click: function () {
                            RisarEventControlService.open_edit_modal(event, self.urls)
                                .then(function () {
                                    $window.location.replace(self.urls.html + '?event_id=' + event.id);
                                })
                        },
                        text: 'Изменить'
                    },
                    ' ',
                    {
                        click: function () {
                            self.delete(ticket_id, event.id).then(function success() {
                                $window.location.replace(self.urls.back);
                            })
                        },
                        text: 'Отменить'
                    }
                ],
                'success'
            );
    };
    this.maternal_cert = {
        get_by_event: function (event_id) {
            return wrapper('GET', Config.url.api_maternal_cert_for_event.format(event_id))
        },
        save: function (cert) {
            var target_url = cert.id === undefined ? Config.url.api_maternal_cert_save : Config.url.api_maternal_cert_save + cert.id;
            return wrapper('POST', target_url, {}, cert)
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
        get_copy: function (event_id, checkup_id) {
            return wrapper('GET', Config.url.api_checkup_get_copy.format(event_id, checkup_id));
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
    this.checkup_gyn = {
        get_list: function (event_id) {
            return wrapper('GET', Config.url.gyn.checkup_list.format(event_id));
        },
        get: function (event_id, checkup_id) {
            return wrapper('GET', Config.url.gyn.checkup.format(event_id, checkup_id));
        },
        create: function (event_id, flat_code) {
            return wrapper('GET', Config.url.gyn.checkup_new.format(event_id, flat_code));
        },
        save: function (event_id, data) {
            return wrapper('POST', Config.url.gyn.checkup_post.format(event_id), {}, data);
        }
    };
    this.fetus = {
        get_fetus_list: function (event_id) {
            return wrapper('GET', Config.url.api_fetus_list + event_id);
        },
        calc_fisher_ktg: function (fetus_data) {
            return wrapper('POST', Config.url.api_fetus_calc_fisher_ktg, {}, fetus_data, {
                silent: true
            });
        }
    };
    this.gravidograma = {
        get: function (event_id){
            return wrapper('GET', Config.url.api_gravidograma + event_id);
        }
    };
    var _anamnesis_base = {
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
        },
        pregnancies: {
            get: function (event_id, id) {
                return wrapper('GET', Config.url.api_anamnesis_pregnancies.format(event_id, id));
            },
            delete: function (event_id, id) {
                return wrapper('DELETE', Config.url.api_anamnesis_pregnancies.format(event_id, id));
            },
            undelete: function (event_id, id) {
                return wrapper('POST', Config.url.api_anamnesis_pregnancies_undelete.format(event_id, id));
            },
            save: function (event_id, data) {
                return wrapper('POST', Config.url.api_anamnesis_pregnancies.format(event_id, data.id || ''), undefined, data);
            }
        }
    };
    this.gynecological_anamnesis = _.extend({}, _anamnesis_base, {
        get: function (event_id) {
            var url = Config.url.gyn.anamnesis.format(event_id);
            return wrapper('GET', url);
        },
        general: {
            get: function (event_id) {
                return wrapper('GET', Config.url.gyn.anamnesis_general.format(event_id));
            },
            save: function (event_id, data) {
                return wrapper('POST', Config.url.gyn.anamnesis_general.format(event_id), {}, data);
            }
        }
    });
    this.anamnesis = _.extend({}, _anamnesis_base, {
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
        }
    });
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
        get_by_action: function (action_id, args) {
            return wrapper('GET', Config.url.api_measure_list_by_action + action_id, args)
        },
        regenerate: function (action_id) {
            return wrapper('GET', Config.url.api_event_measure_generate + action_id)
        },
        get: function (event_measure_id, args) {
            var url = Config.url.api_event_measure_get;
            if (event_measure_id) {
                url += event_measure_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        get_info: function (event_measure_id, args) {
            return wrapper('GET', Config.url.api_event_measure_get_info.format(event_measure_id), args)
        },
        save_list: function (event_id, data) {
            return wrapper('POST', Config.url.api_event_measure_save_list.format(event_id), {}, data);
        },
        execute: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_execute + event_measure_id);
        },
        cancel: function (event_measure_id, data) {
            return wrapper('POST', Config.url.api_event_measure_cancel + event_measure_id, {}, data);
        },
        del: function (event_measure_id) {
            return wrapper('DELETE', Config.url.api_event_measure_delete.format(event_measure_id));
        },
        restore: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_undelete.format(event_measure_id));
        },
        get_checkups: function (event_measure_id) {
            return wrapper('POST', Config.url.api_event_measure_checkups + event_measure_id);
        },
        new_appointment: function (client_id, person_id, start_date) {
            var external_url = WMConfig.local_config.risar.schedule.external_schedule_url;
            this.child_window = $window.open(
                external_url ||
                Config.url.url_schedule_appointment_html +
                    '?client_id=' + client_id +
                    '&person_id=' + person_id +
                    '&start_date=' + start_date,
                '_blank'
            );
        },
        get_appointment: function (event_measure_id, appointment_id, args) {
            var url = Config.url.api_event_measure_appointment_get.format(event_measure_id);
            if (appointment_id) {
                url += appointment_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
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
                    return $q.reject(result);
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
                    return $q.reject(result);
                });
        },
        save_appointment_list: function (action_id, em_id_list) {
            var url = Config.url.api_event_measure_appointment_list_save.format(action_id),
                data = {em_id_list: em_id_list};
            return wrapper('POST', url, {}, data)
                .then(function (result) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return result;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
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
        get_radz_risk_info: function (curation_level_code) {
            return wrapper('GET', Config.url.api_stats_radz_risks, {
                curation_level_code: curation_level_code
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
        },
        controlled_events: function(curation_level_code) {
            return wrapper('GET', Config.url.api_stats_controlled_events, {
                curation_level_code: curation_level_code
            })
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
    this.radzinsky_risks = {
        list: function (event_id) {
            return wrapper('GET', Config.url.api_chart_radzinsky_risks.format(event_id));
        },
        print: function (query) {
            self.file_get('POST', Config.url.api_radz_print, query);
        }
    };
    this.soc_prof_help = {
        save: function(event_id, flat_code, data) {
            return wrapper('POST', Config.url.api_soc_prof_help.format(data.id||'', flat_code), {event_id: event_id}, data);
        },
        get_list: function(event_id) {
            return wrapper('GET', Config.url.api_soc_prof_help_list.format(event_id));
        },
        delete: function (id) {
            return wrapper('DELETE', Config.url.api_soc_prof_help_delete.format(id));
        },
        undelete: function (id) {
            return wrapper('POST', Config.url.api_soc_prof_help_undelete.format(id));
        }
    };
    this.partal_nursing = {
        save: function(pp_id, flatcode, event_id, data) {
            return wrapper('POST', Config.url.api_partal_nursing.format(flatcode, pp_id||''), {event_id: event_id}, data);
        },
        get: function(flatcode, nursing_id, event_id) {
            return wrapper('GET', Config.url.api_partal_nursing.format(flatcode, nursing_id), {event_id: event_id});
        },
        get_list: function(flatcode, event_id) {
            return wrapper('GET', Config.url.api_partal_nursing_list.format(flatcode, event_id));
        },
        delete: function (id) {
            return wrapper('DELETE', Config.url.api_partal_nursing_delete.format(id));
        },
        undelete: function (id) {
            return wrapper('POST', Config.url.api_partal_nursing_undelete.format(id));
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
    this.ambulance = {
        get: function(event_id){
            return wrapper('GET', Config.url.api_ambulance.format(event_id));
        }
    };
}]);
WebMis20.controller('RisarHeaderCtrl', ['$scope', 'RisarApi', 'CurrentUser', 'RefBookService', 'ErrandModalService',
    'ChartTransferModalService', 'DateRegistrationModalService',
function ($scope, RisarApi, CurrentUser, RefBookService, ErrandModalService, ChartTransferModalService, DateRegistrationModalService) {
    $scope.openTransferModal = function () {
        ChartTransferModalService.openTransfer($scope.header.event.id).then(function(rslt){
            $scope.header = rslt;
        });
    };
    $scope.openDateRegistrationModal = function () {
        DateRegistrationModalService.openDateRegistration($scope.header.event).then(function(header){
            if (header) {
                $scope.header = header;
            }
        });
    };
    $scope.create_errand = function () {
        var errand = {
            event_id: $scope.header.event.id,
            set_person: CurrentUser.info,
            communications: '',
            exec_person: $scope.header.event.person,
            event: {external_id: $scope.header.event.external_id},
            status: $scope.rbErrandStatus.get_by_code('waiting')
        };

        RisarApi.utils.get_person_contacts(errand.set_person.id).then(function (contacts) {
            errand.communications = contacts;
            ErrandModalService.openNew(errand, true)
                .then()
        });
    };
    $scope.init = function () {
        $scope.rbErrandStatus = RefBookService.get('ErrandStatus');
    };
    $scope.init();
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
.directive('radzRiskRateIcon', ['$window', 'Config', function ($window, Config) {
    return {
        restrict: 'A',
        template: '\
<span style="font-size: 60%; vertical-align: super" class="label" ng-class="icon_class()" tooltip="[[ get_tooltip() ]]"\
    >Р</span>\
',
        scope: {
            radzRiskRateIcon: '='
        },
        link: function (scope, element, attrs) {
            scope.icon_class = function () {
                if (!scope.radzRiskRateIcon) return;
                var r = scope.radzRiskRateIcon;
                if (r.code === 'low') return 'label-success';
                else if (r.code === 'medium') return 'label-warning';
                else if (r.code === 'high') return 'label-danger';
                return 'label-default';
            };
            scope.get_tooltip = function () {
                if (!scope.radzRiskRateIcon) return;
                return scope.radzRiskRateIcon.name;
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
                controller: 'ErrandModalCtrl',
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
                    controller: 'ErrandModalCtrl',
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
.service('RisarEventControlService', ['$modal', 'ApiCalls', function ($modal, ApiCalls) {
    return {
        open_edit_modal: function (event, urls) {
            var model = {
                beg_date: event.set_date,
                person: event.person
            };
            return $modal.open({
                template: '\
<div class="modal-header">\
    <h3 class="modal-title">Изменение данных карты</h3>\
</div>\
<div class="modal-body">\
    <h1>Изменение данных карты</h1>\
    <div class="row">\
        <div class="col-md-4">Дата создания карты</div>\
        <div class="col-md-8"><wm-date ng-model="$model.beg_date" min-date="minDate" max-date="currentDate" /></div>\
    </div>\
    <div class="row">\
        <div class="col-md-4">Лечащий врач</div>\
        <div class="col-md-8"><wm-person-select ng-model="$model.person" /></div>\
    </div>\
</div>\
<div class="modal-footer">\
    <button class="btn btn-success" ng-click="$close()">Сохранить</button>\
    <button class="btn btn-default" ng-click="$dismiss()">Отменить</button>\
</div>',
                controller: function ($scope, $modalInstance) {
                    $scope.$model = model;
                    $scope.currentDate = new Date();
                    $scope.minDate = event.client.birth_date;
                },
                size: 'lg'
            }).result.then(function () {
                ApiCalls.wrapper(
                    'PATCH',
                    urls.get.format(event.id),
                    undefined,
                    model
                ).then(function (ret_event) {
                    _.extend(event, ret_event)
                })
            })
        }
    }
}])
.service('ChartTransferModalService', ['$modal', '$q', 'RisarApi', 'RefBookService', function ($modal, $q, RisarApi, RefBookService) {
    return {
        openTransfer: function (event_id) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/chart_transfer.html',
                template: '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
        <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
        <h4 class="modal-title">Перевод пациентки к другому врачу</h4>\
    </div>\
    <div class="modal-body">\
        <div class="das-form">\
        <ng-form name="MCForm">\
              <table class="table table-condensed">\
                   <thead>\
                       <tr>\
                           <th class="col-md-3"></th>\
                           <th class="col-md-9"></th>\
                       </tr>\
                   </thead>\
                    <tbody>\
                        <tr>\
                            <td class="text-right"><strong>ЛПУ</strong></td>\
                            <td>\
                                <div class="col-lg-8 col-md-8 col-xs-6">\
                                    <ui-select ng-required="true" ng-model="model.org" ng-change="onOrgChanged()" theme="select2" class="form-control" name="LPU" ref-book="Organisation" autocomplete="off">\
                                        <ui-select-match placeholder="не выбрано">[[ $select.selected.short_name ]]</ui-select-match>\
                                        <ui-select-choices repeat="item in $refBook.objects | organisation_filter | filter: $select.search | limitTo: 50">\
                                            <span ng-bind-html="item.full_name | highlight: $select.search"></span>\
                                        </ui-select-choices>\
                                    </ui-select>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <td class="text-right"><strong>Врач</strong></td>\
                            <td>\
                                 <div class="col-lg-8 col-md-8 col-xs-6">\
                                  <ui-select ng-required="true" ng-model="model.person" theme="select2" class="form-control" name="maternity_hosp_medico" ref-book="Person" autocomplete="off">\
                                    <ui-select-match placeholder="не выбрано">[[ $select.selected.short_name ]]</ui-select-match>\
                                    <ui-select-choices repeat="item in filteredMedicos | filter: $select.search | limitTo: 50">\
                                        <span ng-bind-html="item.full_name | highlight: $select.search"></span>\
                                    </ui-select-choices>\
                                    </ui-select>\
                                 </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <td class="text-right"><strong>Дата</strong></td>\
                            <td>\
                                <div class="col-lg-8 col-md-8 col-xs-6"><wm-date max-date="currentDate" ng-model="model.ep_date" ng-required="true" autofocus></wm-date></div>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
        </ng-form>\
        </div>\
    </div>\
   <div class="modal-footer">\
       <button type="button" class="btn btn-primary" ng-disabled="MCForm.$invalid" ng-click="saveAndClose()">Сохранить</button>\
       <button type="button" class="btn btn-default" ng-click="$dismiss()">Отменить</button>\
    </div>',
                backdrop: 'static',
                controller: function ($scope, $modal, RisarApi, event_id) {
                    $scope.currentDate = new Date();
                    $scope.model = {};
                    $scope.filteredMedicos = [];

                    $scope.loadOwnMedicos = function() {
                        var orgId = $scope.model.org.id;
                        $scope.filteredMedicos = safe_traverse($scope, ['groupedMedicos', orgId]);
                    };
                    $scope.onOrgChanged = function() {
                        $scope.loadOwnMedicos();
                        $scope.model.person = null;
                    };
                    $scope.saveAndClose = function() {
                        RisarApi.chart.transfer(event_id, $scope.model.person.id, {beg_date: $scope.model.ep_date}).then(function(resp) {
                            $scope.$close(resp);
                        });
                    };
                    var reload = function () {
                        $scope.allMedicos = RefBookService.get('Person');
                        var head_promise = RisarApi.chart.get_header(event_id);
                        $q.all([$scope.allMedicos.loading, head_promise]).then(function (result) {
                            var header_data = result[1];
                            $scope.groupedMedicos = _.groupBy($scope.allMedicos.objects, function(obj) {
                                return obj.organisation != undefined ? obj.organisation.id: null
                            });
                            $scope.model = {
                                person: header_data.header.event.person,
                                org: header_data.header.event.person.organisation,
                                ep_date: new Date()
                            };
                            $scope.loadOwnMedicos();
                        });

                    };
                    reload();
                },
                size: 'lg',
                resolve: {
                    event_id: function () {
                        return event_id
                    }
                }
            });
            return instance.result
        }
    }
}])
.service('DateRegistrationModalService', ['$modal', 'RisarApi', function ($modal, RisarApi) {
    return {
        openDateRegistration: function (event) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/date_registration.html',
                template: '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
        <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
        <h4 class="modal-title">Изменить дату постановки на учет по беременности</h4>\
        </div>\
        <div class="modal-body">\
            <div class="das-form">\
            <ng-form name="MCForm">\
                  <table class="table table-condensed">\
                        <tbody>\
                            <tr>\
                                <td class="text-right"><strong>Дата</strong></td>\
                                <td>\
                                    <div class="col-lg-8 col-md-8 col-xs-6"><wm-date max-date="currentDate" ng-model="model.set_date" ng-required="true" autofocus></wm-date></div>\
                                </td>\
                            </tr>\
                        </tbody>\
                    </table>\
            </ng-form>\
            </div>\
        </div>\
       <div class="modal-footer">\
           <button type="button" class="btn btn-primary" ng-click="saveAndClose()">Сохранить</button>\
           <button type="button" class="btn btn-default" ng-click="$dismiss()">Отменить</button>\
        </div>',
                backdrop: 'static',
                controller: function ($scope, $modal, RisarApi, event) {
                    $scope.model = {
                        set_date: event.set_date
                    };
                    $scope.currentDate = new Date();
                    $scope.saveAndClose = function() {
                        var old_date = moment(event.set_date).startOf('day');
                        var new_date = moment($scope.model.set_date).startOf('day');
                        if (new_date.isSame(old_date)) {
                            $scope.$close();
                        }
                        RisarApi.chart.update_set_date(event.id, {set_date: new_date.toDate()}).then(function(resp) {
                            $scope.$close(resp);
                        });
                    };
                },
                size: 'lg',
                resolve: {
                    event: function () {
                        return event
                    }
                }
            });
            return instance.result
        }
    }
}])
.directive('extSelectQuickEventSearch', ['$http', '$window', 'Config', function ($http, $window, Config) {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match  placeholder="[[placeholder]]">[[ $select.selected.client_name ]]</ui-select-match>\
<ui-select-choices repeat="client in clients" refresh="refresh_list($select.search)">\
    <div  ng-switch="client.event_type_code">\
        <span  ng-bind-html="client.client_name | highlight: $select.search"></span>\
        <strong>[[ client.external_id ]] </strong>                                                                                                                                  \
        <span ng-switch-when="98">Карта беременной</span>\
        <span ng-switch-when="97">Карта амбулаторного пациента</span>\
    </div>\
</ui-select-choices> ');
            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    scope.placeholder = iAttrs.placeholder || 'ФИО пациента';
                    scope.autoChartUrl = Config.url.chart_auto_html + '?event_id=';
                    scope.onRefresh = scope.$eval(iAttrs.onRefresh) || angular.noop;

                    scope.goToCard = function (event_id) {
                        $window.location.href = scope.autoChartUrl+event_id;
                    };
                    scope.onSelect = function(){
                        var event_id = safe_traverse(arguments, ['0', 'id']);
                        if (event_id !== undefined) {
                            scope.goToCard(event_id);
                        }
                    };
                    scope.refresh_list = function (query) {
                        scope.onRefresh(query);
                        scope.get_clients(query);
                    };
                    scope.get_clients = function (query) {
                        if (!query) return;
                        return $http.get(Config.url.api_event_search_short, {
                            params: {
                                q: query,
                                limit: 20
                            }
                        })
                        .then(function (res) {
                            return scope.clients = res.data.result;
                        });
                    };
                }
            }
        }
    }
}])
.directive('clickAndGo', ["$window", function ($window) {
        return {
            scope: {
                uri: '@'
            },
            link: function (scope, element, attrs) {
                element.bind('click', function(e) {
                    scope.$apply(function() {
                        $window.open(attrs.uri, '_self');
                    });
                });

            }
        }
}])
.directive('wmBtnControlEvent', ['RisarApi', 'NotificationService', function (RisarApi, NotificationService) {
    return {
        restrict: 'E',
        scope: {
            eventId: '=',
            isControlled: '='
        },
        template: '\
<a href="javascript:void(0);" ng-click="toggle()"\
    tooltip="[[isControlled ? \'Карта взята на контроль\' : \'Взять карту на контроль\']]">\
    <i class="fa text-yellow" ng-class="{\'fa-star\': isControlled, \'fa-star-o\': !isControlled}"></i>\
</a>',
        link: function (scope, iElement, iAttr) {
            scope.toggle = function () {
                if (scope.isControlled) {
                    RisarApi.chart.remove_control(scope.eventId)
                        .then(function (result) {
                            scope.isControlled = result.controlled;
                            NotificationService.notify(200,
                                'Пациентка снята с контроля',
                                'info', 5000);
                        });
                } else {
                    RisarApi.chart.take_control(scope.eventId)
                        .then(function (result) {
                            scope.isControlled = result.controlled;
                            NotificationService.notify(200,
                                'Пациентка взята на контроль',
                                'info', 5000);
                        });
                }
            };
        }
    }
}])
;