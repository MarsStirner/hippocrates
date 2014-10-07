/**
 * Created by mmalkov on 11.07.14.
 */
var DaySetupModalCtrl = function ($scope, $modalInstance, selected_days, model, rec_types, roas, offices, tq_types) {
    $scope.rec_types = rec_types;
    $scope.roas = roas;
    $scope.offices = offices;
    $scope.tq_types = tq_types;

    $scope.selected_days = selected_days;
    $scope.model = model;
    $scope.absent = {
        checked: model.roa !== null
    };

    $scope.accept = function () {
        var interval_altered = this.intervalsSetupForm.$dirty || this.roaForm.$dirty;
        var quoting_altered = this.quotingSetupForm.$dirty;

        var selected_days = $scope.selected_days.map(function(day) {
                return day.selected ? day.date : undefined;
            }),
            result = {
                selected_days: selected_days,
                model: $scope.model,
                interval_altered: interval_altered,
                quoting_altered: quoting_altered
            };
        $modalInstance.close(result);
    };
    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
    $scope.absent_checked = function () {
        if (!$scope.absent.checked) {
            $scope.model.roa = null;
        }
    };
    $scope.add_new_interval = function() {
        $scope.model.intervals.push({
            begTime: moment('09:00', "HH:mm:ss").toDate(),
            endTime: moment('15:00', "HH:mm:ss").toDate(),
            office: $scope.model.default_office,
            reception_type: null,
            CITO: 0,
            planned: 0,
            extra: 0
        });
        $scope.sync_times();
    };
    $scope.delete_interval = function(interval) {
        $scope.model.intervals.remove(interval);
        this.intervalsSetupForm.$dirty = true;
        $scope.sync_times();
    };
    $scope.add_new_quota = function() {
        $scope.model.quotas.push({
            time_start: moment('00:00', "HH:mm:ss").toDate(),
            time_end: moment('00:00', "HH:mm:ss").toDate(),
            reception_type: null
        });
//        $scope.sync_times();
    };
    $scope.delete_quota = function(quota) {
        $scope.model.quotas.remove(quota);
        this.quotingSetupForm.$dirty = true;
//        $scope.sync_times();
    };
    // timepicker validation, TODO: directive
    $scope.times_valid = true;
    $scope.sync_times = function() {
        var i_list = $scope.model.intervals.map(function (interval) {
            return {
                begTime: interval.begTime,
                endTime: interval.endTime
            };
        }).sort(function (a, b) {
            if (a.begTime < b.begTime) { return -1; }
            else if (a.begTime > b.begTime) { return 1; }
            else { return 0; }
        });
        var cur_interval,
            prev_interval,
            valid = true;
        for (var i = 0; i < i_list.length; i += 1) {
            cur_interval = i_list[i];
            prev_interval = i !== 0 ? i_list[i - 1] : undefined;
            valid = (
                (cur_interval.begTime < cur_interval.endTime) &&
                (prev_interval === undefined ? true :
                    !((prev_interval.begTime <= cur_interval.begTime && cur_interval.begTime <= prev_interval.endTime) ||
                        (cur_interval.endTime <= prev_interval.endTime && prev_interval.begTime <= cur_interval.endTime))
                    )
                );
            if (!valid) break;
        }
        $scope.times_valid = valid;
    };
};
var DayFreeModalCtrl = function ($scope, $modalInstance, day, roas) {
    $scope.day = day;
    $scope.roa = day.roa ? (day.roa.code) : (null);
    $scope.accept = function () {
        $modalInstance.close(this.roa);
    };
    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
    $scope.roas = roas;
};
var ScheduleMonthCtrl = function ($scope, $http, $modal, RefBook, PersonTreeUpdater, $location) {
    $scope.reception_types = new RefBook('rbReceptionType');
    $scope.rbReasonOfAbsence = new RefBook('rbReasonOfAbsence');
    $scope.rbTimeQuotingType = new RefBook('rbTimeQuotingType');
    $scope.offices = new RefBook('Office');
    $scope.editing = false;
    $scope.weekends_selectable = false;
    $scope.selected_days = [];
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.person_id = $scope.params.person_id;
    $scope.person_query = '';
    var curDate = new Date();
    var curYear = curDate.getUTCFullYear();
    $scope.years = [curYear - 1, curYear, curYear + 1];
    $scope.year = curYear;

    $scope.month = curDate.getMonth();
    $scope.prevMonthsInfo = [];

    $scope.weekdays = ['Пн', "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    $scope.week_data = [];
    $scope.quotas_by_week = [];


    $scope.reloadSchedule = function () {
        if ($scope.person_id) {
            $http.get(
                url_schedule_api_schedule_description, {
                    params: {
                        person_id: $scope.person_id,
                        start_date: $scope.monthDate.format('YYYY-MM'),
                        expand: 1
                    }
                }
            ).success(make_schedule);
        }
    };

    function make_schedule (data) {
        $scope.person = data.result['person'];
        $scope.schedules = data.result['schedules'];
        $scope.quotas = data.result['quotas'];
        make_week();
    }

    var make_week = function () {
        var first_weekday = $scope.monthDate.weekday();
        var day_iter = 0;
        var schedule = $scope.schedules;
        var quotas = $scope.quotas;
        var result = [];
        var quotas_result = [];
        for (var week_n = 0; ; week_n++) {
            var week = [];
            var quota_week = [];
            for (var weekday_n = 0; weekday_n < 7; weekday_n++) {
                if (week_n == 0 && weekday_n < first_weekday || day_iter >= schedule.length) {
                    week.push({
                        not_exists: true
                    });
                    quota_week.push({
                        not_exists: true
                    })
                } else {
                    week.push(schedule[day_iter]);
                    quota_week.push(quotas[day_iter]);
                    day_iter++;
                }
            }
            result.push(week);
            quotas_result.push(quota_week);
            if (day_iter >= schedule.length) {
                break;
            }
        }
        $scope.week_data = result;
        $scope.quotas_by_week = quotas_result;
    };

    function month_is_empty() {
        return !($scope.schedules.some(function (schedule) {
            return schedule.roa || schedule.scheds.length; // todo: || Object.keys(schedule.info).length
        }) || $scope.quotas.some(function (quota) {
            return quota.day_quotas.length;
        }));
    }

    $scope.monthChanged = function () {
        $scope.monthDate = moment({
            year: $scope.year,
            month: $scope.month,
            day: 1
        });
        $scope.reloadSchedule();
        $scope.updatePreviousMonthsInfo();
        PersonTreeUpdater.set_schedule_period(
            $scope.monthDate.clone().toDate(),
            $scope.monthDate.clone().endOf('month').toDate()
        );
    };

    $scope.updatePreviousMonthsInfo = function () {
        $scope.prevMonthsInfo = aux.range(2, 7).map(function (m_offset) {
            var p_month = moment($scope.monthDate).subtract(m_offset, 'months'),
                fmt = p_month.year() === $scope.monthDate.year() ? 'MMMM' : 'MMMM (YYYY)';
            return {
                date: p_month,
                name: p_month.format(fmt)
            };
        });
    };

    $scope.start_editing = function () {
        $scope.editing = true;
    };

    $scope.finish_editing = function () {
        $http.post(
            url_schedule_api_schedule_description_post, {
                person_id: $scope.person_id,
                schedule: $scope.schedules.filter(function (day) {
                    return day.altered;
                }),
                quotas: $scope.quotas.filter(function (quota) {
                    return quota.altered;
                }),
                start_date: $scope.monthDate.format('YYYY-MM')
            }
        ).success(function (data) {
            $scope.editing = false;
            $scope.selected_days = [];
            make_schedule(data);
        }).error(function (response) {
            var msg = 'Ошибка сохранения расписания';
            if (response.meta && response.meta.name) {
                msg = '{0}: "{1}".'.format(msg, response.meta.name);
            }
            alert(msg);
        });
    };

    $scope.cancel_editing = function () {
        $scope.editing = false;
        $scope.reloadSchedule();
        $scope.selected_days = [];
    };

    $scope.monthChanged();

    $scope.$watch('person_id', function (new_value, old_value) {
        if (!new_value || new_value == old_value) return;
        var path = $location.path() + '?person_id=' + new_value;
        $location.url(path).replace();
        window.history.pushState(null, document.title, location.origin + location.pathname + '?person_id=' + new_value);
        $scope.reloadSchedule();
    });

    var day_selected = function (day) {
        return $scope.selected_days.indexOf(day) !== -1;
    };

    var day_selectable = function (day) {
        return !day.busy && ($scope.weekends_selectable || moment(day.date).weekday() < 5)
    };

    $scope.select = {
        day: function (day) {
            if (!$scope.editing) return;
            if (!day_selectable(day)) return;
            var index = $scope.selected_days.indexOf(day);
            if (index !== -1) {
                $scope.selected_days.splice(index, 1);
            } else {
                $scope.selected_days.push(day);
            }
        },
        week: function (week) {
            if (!$scope.editing) return;
            var weekdays = week.filter(function (day) {
                return !day.not_exists;
            });
            var weekdays_unselected = weekdays.filter(day_selectable).filter(function (day) {
                return $scope.selected_days.indexOf(day) === -1;
            });
            var select = weekdays_unselected.length > 0;
            if (select) {
                $scope.selected_days = $scope.selected_days.concat(weekdays_unselected.filter(day_selectable));
            } else {
                $scope.selected_days = $scope.selected_days.filter(aux.func_not_in(weekdays));
            }
        },
        odd: function () {
            $scope.selected_days = $scope.schedules.filter(day_selectable).filter(function (day) {
                return moment(day.date).date() % 2 !== 0
            })
        },
        invert: function () {
            $scope.selected_days = $scope.schedules.filter(aux.func_not_in($scope.selected_days)).filter(day_selectable);
        },
        all: function () {
            $scope.selected_days = $scope.schedules.filter(day_selectable);
        },
        none: function () {
            $scope.selected_days = [];
        }
    };

    $scope.fill_selection = function () {
        var modalInstance = $modal.open({
            templateUrl: 'modal-DaysSetup.html',
            size: 'lg',
            controller: DaySetupModalCtrl,
            resolve: {
                selected_days: function() {
                    return $scope.selected_days.map(function(day) {
                        return {
                            date: day.date,
                            selected: true
                        };
                    });
                },
                model: function () {
                    var first_day_shedule = $scope.selected_days[0];
                    var first_day_quotas = $scope.quotas.filter(function(day_quotas){return day_quotas.date == first_day_shedule.date})[0];
                    return {
                        roa: first_day_shedule.roa,
                        intervals: first_day_shedule.scheds.map(function(interval) {
                            return {
                                begTime: moment(interval.begTime, "HH:mm:ss").toDate(), // utc dates in model, local on screen
                                endTime: moment(interval.endTime, "HH:mm:ss").toDate(),
                                office: interval.office, // copy? why no need?
                                reception_type: interval.reception_type,
                                CITO: interval.CITO,
                                planned: interval.planned,
                                extra: interval.extra
                            }
                        }),
                        quotas: first_day_quotas.day_quotas.map(function(quota) {
                            return {
                                time_start: moment(quota.time_start, "HH:mm:ss").toDate(), // utc dates in model, local on screen
                                time_end: moment(quota.time_end, "HH:mm:ss").toDate(),
                                quoting_type: quota.quoting_type
                            }
                        }),
                        default_office: $scope.person.office
                    };
                },
                rec_types: function() {
                    return $scope.reception_types.objects;
                },
                roas: function () {
                    return $scope.rbReasonOfAbsence.objects;
                },
                offices: function () {
                    return $scope.offices.objects;
                },
                tq_types: function () {
                    return $scope.rbTimeQuotingType.objects;
                }
            }
        });
        modalInstance.result.then(function(result) {
            var processed_days = $scope.selected_days.filter(function(day_schedule) {
                return result.selected_days.has(day_schedule.date); // strings
            });
            var prosessed_quotas = $scope.quotas.filter(function(day_quotas) {
                return result.selected_days.has(day_quotas.date); // strings
            });

            var model = result.model;
            if (result.interval_altered){
                processed_days.forEach(function(day) {
                    day.altered = true;
                    day.roa = model.roa;
                    if (model.roa) {
                        day.scheds = [];
                    } else {
                        day.scheds = model.intervals.map(function(interval) {
                            return {
                                begTime: moment(interval.begTime).format("HH:mm:ss"),
                                endTime: moment(interval.endTime).format("HH:mm:ss"),
                                office: interval.office,
                                reception_type: interval.reception_type,
                                CITO: interval.CITO,
                                planned: interval.planned,
                                extra: interval.extra
                            };
                        });
                    }
                });
            }

            if (result.quoting_altered) {
                prosessed_quotas.forEach(function(quota) {
                    quota.altered = true;
                    quota.day_quotas = model.quotas.map(function(quota) {
                        return {
                            time_start: moment(quota.time_start).format("HH:mm:ss"),
                            time_end: moment(quota.time_end).format("HH:mm:ss"),
                            quoting_type: quota.quoting_type
                        };
                    });
                });
            }

            $scope.select.none();
        });
    };

    $scope.free_up_day = function (day) {
        var instance = $modal.open({
            templateUrl: 'modal-DayFree.html',
            controller: DayFreeModalCtrl,
            resolve: {
                day: function () {
                    return day;
                },
                roas: function () {
                    return $scope.rbReasonOfAbsence.objects
                }
            }
        });
        instance.result.then(function (roa) {
            $http.post(url_schedule_api_schedule_lock, {
                person_id: $scope.person_id,
                date: day.date,
                roa: roa
            }).success(function () {
                window.open(url_schedule_api_html_day_free +
                '?person_id=' + $scope.person_id +
                '&date=' + day.date,
                    '_self');
            });
        })
    };

    $scope.copy_schedule_from_previous_month = function (from_date) {
        if (!month_is_empty()) {
            return alert('На месяц уже заведено расписание или указано квотирование по времени. ' +
                'Чтобы копировать расписание с предыдущего месяца удалите существующее расписание и информацию о квотах.');
        }
        if (from_date === undefined) {
            from_date = $scope.monthDate.clone().subtract(1, 'months');
        }
        var from_start_date = from_date.clone().startOf('month'),
            from_end_date = from_date.clone().endOf('month'),
            to_start_date = $scope.monthDate.clone().startOf('month'),
            to_end_date = $scope.monthDate.clone().endOf('month');

        $http.get(
            url_api_copy_schedule_description, {
                params: {
                    person_id: $scope.person_id,
                    from_start_date: from_start_date.format('YYYY-MM-DD'),
                    from_end_date: from_end_date.format('YYYY-MM-DD'),
                    to_start_date: to_start_date.format('YYYY-MM-DD'),
                    to_end_date: to_end_date.format('YYYY-MM-DD')
                }
            }
        ).success(make_schedule);
    };

    $scope.get_day_class = function (day, index) {
        var result = [];
        if ($scope.editing) {
            if (day_selectable(day)) {
                result.push('day-selectable');
            }
            if (day_selected(day)) {
                result.push('panel-primary')
            } else if (index >= 5 || day.roa) {
                result.push('panel-danger')
            } else {
                result.push('panel-default')
            }
        } else {
            if (day.scheds.length > 0) {
                result.push('panel-success');
            } else if (index >= 5 || day.roa) {
                result.push('panel-danger')
            } else {
                result.push('panel-default')
            }
        }
        return result;
    };

    $scope.person_schedule_day_switch = function (day) {
        if (day.roa) {
            return 'absent';
        } else if (day.scheds.length > 0) {
            return 'normal';
        } else {
            return 'empty';
        }
    };

    $scope.getRecTypeText = function(rt_code, icon) {
        if (arguments.length < 2) {
            icon = false;
        }
        var text = '',
            rt_text = '',
            icon_text = '';
        switch(rt_code) {
            case 'amb':
                rt_text = 'Амбулаторный приём';
                icon_text = 'plus';
                break;
            case 'home':
                rt_text = 'Приём на дому';
                icon_text = 'home';
                break;
        }
        text = [icon ? '<span class="glyphicon glyphicon-' + icon_text + '"></span>' : '',
                '<nobr>' + '&nbsp;' + rt_text + '</nobr>'].join('');
        return text;
    };
};
WebMis20.controller('ScheduleMonthCtrl', ['$scope', '$http', '$modal', 'RefBook', 'PersonTreeUpdater', '$location', ScheduleMonthCtrl]);
