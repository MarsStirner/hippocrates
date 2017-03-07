/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventSearchCtrl = function ($scope, $q, RisarApi, TimeoutCallback, RefBookService, CurrentUser, WMConfig) {
    var default_docs = [{
        full_name: 'Все',
        name: 'Все'
    }];
    $scope.closed_items = [{
        name: 'Все'
    }, {
        name: 'Закрытые',
        value: true
    }, {
        name: 'Открытые',
        value: false
    }];
    /* Значения взяты из CardFillRate */
    $scope.card_fill_rate = [{
        name: 'Все'
    }, {
        name: 'Заполнена',
        value: 2
    }, {
        name: 'Не заполнена',
        value: 3
    }];
    $scope.card_sections = [{
        name: 'Карта целиком',
        value: 'card_completely'
    }, {
        name: 'Анамнез',
        value: 'anamnesis'
    }, {
        name: 'Первичный осмотр',
        value: 'first_inspection'
    }, {
        name: 'Вторичный осмотр',
        value: 'repeated_inspection'
    }, {
        name: 'Эпикриз',
        value: 'epicrisis'
    }];
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.request_types = [];
    $scope.$watchCollection('rbRequestType.objects', function (n, o) {
        if (!_.isArray(n) || _.isEqual(n, o)) return;
        $scope.request_types = _.filter(n, function (i) {
            return _.contains(['gynecological', 'pregnancy'], i.code)
        })
    });

    $scope.risks_rb = RefBookService.get('PerinatalRiskRate');
    $scope.radz_risks_rb = RefBookService.get('rbRadzinskyRiskRate');
    $scope.pathology_rb = RefBookService.get('PregnancyPathology');
    $scope.rbRisarRiskGroup = RefBookService.get('rbRisarRiskGroup');
    $scope.rbMeasureType = RefBookService.get('rbMeasureType');

    $scope.results = [];
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
    };
    $scope.query = {
        areas: [],
        curators: [],
        orgs: [],
        person: default_docs[0],
        fio: null,
        checkup_date_from: null,
        checkup_date_to: null,
        bdate_from: null,
        bdate_to: null,
        risk: [],
        radz_risk: [],
        closed: $scope.closed_items[0],
        client_work_group: {},
        fertilization_type: {},
        age_min: null,
        age_max: null,
        request_types: [],
        preg_week_min: null,
        preg_week_max: null,
        latest_inspection_gt: null,
        pathology: [],
        risk_groups: [],
        epicrisis_delivery_date_gt: null,
        card_fill: $scope.card_fill_rate[0],
        card_section: $scope.card_sections[0],
        mkbs: [],
        closed_diags: null,
        overdue: null,
        measure_type: $scope.rbMeasureType.objects[0],
        controlled_events: null,
        missed_last_checkup: null
    };

    $scope.get_search_data = function () {
        var orgs = [];
        var from_orgs = $scope.query.orgs.length ? $scope.query.orgs: $scope.organisations;
        from_orgs.forEach(function(i) {if(i.id) orgs.push(i.id);});

        var areas = $scope.query.areas,
            curators = $scope.query.curators,
            risks = _.pluck($scope.query.risk, 'id'),
            radz_risks = _.pluck($scope.query.radz_risk, 'id'),
            request_types = _.pluck($scope.query.request_types, 'id'),
            pathologies = _.pluck($scope.query.pathology, 'id'),
            risk_groups = _.pluck($scope.query.risk_groups, 'code'),
            mkbs = _.pluck($scope.query.mkbs, 'id');

        return {
            page: $scope.pager.current_page,
            areas: areas.length ? areas : undefined,
            curators: curators.length ? curators : undefined,
            org_ids: orgs.length ? orgs : undefined,
            doc_id: $scope.query.person.id,
            fio: $scope.query.fio || undefined,
            checkup_date_from: $scope.query.checkup_date_from || undefined,
            checkup_date_to: $scope.query.checkup_date_to || undefined,
            bdate_from: $scope.query.bdate_from || undefined,
            bdate_to: $scope.query.bdate_to || undefined,
            risk: risks.length ? risks : undefined,
            radz_risk: radz_risks.length ? radz_risks : undefined,
            closed: $scope.query.closed.value,
            client_workgroup: $scope.query.client_workgroup || undefined,
            fertilization_type: $scope.query.fertilization_type || undefined,
            age_max: $scope.query.age_max || undefined,
            age_min: $scope.query.age_min || undefined,
            request_types: request_types.length ? request_types : undefined,
            preg_week_min: $scope.query.preg_week_min || undefined,
            preg_week_max: $scope.query.preg_week_max || undefined,
            latest_inspection_gt: (
                _.isNumber($scope.query.latest_inspection_gt) &&
                $scope.query.latest_inspection_gt >= 1 &&
                $scope.query.latest_inspection_gt <= 500
            ) ? $scope.query.latest_inspection_gt : undefined,
            pathology: pathologies.length ? pathologies : undefined,
            risk_groups: risk_groups.length ? risk_groups : undefined,
            epicrisis_delivery_date_gt: (
                _.isNumber($scope.query.epicrisis_delivery_date_gt) &&
                $scope.query.epicrisis_delivery_date_gt >= 1 &&
                $scope.query.epicrisis_delivery_date_gt <= 500
            ) ? $scope.query.epicrisis_delivery_date_gt : undefined,
            card_fill: $scope.query.card_fill.value,
            card_section: $scope.query.card_fill.value !== undefined ? $scope.query.card_section.value : undefined,
            mkbs: mkbs.length ? mkbs : undefined,
            closed_diags: $scope.query.closed_diags || undefined,
            overdue: $scope.query.overdue && $scope.query.measure_type.code,
            controlled_events: $scope.query.controlled_events || undefined,
            missed_last_checkup: $scope.query.missed_last_checkup || undefined
        };
    };

    var perform = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var data = $scope.get_search_data();
        //console.log(JSON.stringify($scope.query));
        //console.log(JSON.stringify(data));
        RisarApi.search_event.get(data).then(function (result) {
            $scope.pager.pages = result.total_pages;
            $scope.pager.record_count = result.count;
            $scope.results = result.events;
        });
    };
    $scope.print_search = function (format){
        var data = $scope.get_search_data();
        data.print_format = format;
        RisarApi.search_event.print(data);
    };
    $scope.group_areas = function (item){
        return $scope.level1[item.parent_code];
    };
    $scope.refresh_areas = function () {
        return RisarApi.search_event.area_list()
        .then(function (result) {
            $scope.level1 = result[0];
            $scope.areas = result[1];
            $scope.query.areas = [];
            return $scope.refresh_curators();
        });
    };
    $scope.refresh_curators = function () {
        var areas = $scope.query.areas.length ? $scope.query.areas : $scope.areas;
        return RisarApi.search_event.area_curator_list(areas)
        .then(function (result) {
            $scope.curators = result;
            $scope.curators_filtered = result.filter(function (item) {
                return CurrentUser.current_role_in('admin') ||
                    item.person_id === CurrentUser.id;
            });
            setFltCurators();
            return $scope.refresh_organisations();
        });
    };
    $scope.refresh_organisations = function () {
        var areas = $scope.query.areas.length ? $scope.query.areas : $scope.areas;
        var curators = $scope.query.curators.length ? $scope.query.curators : $scope.curators;
        return RisarApi.search_event.curator_lpu_list(areas, curators)
        .then(function (result) {
            $scope.organisations = result;
            $scope.query.orgs = [];
            return $scope.refresh_doctors();
        });
    };
    $scope.refresh_doctors = function () {
        var orgs = $scope.query.orgs.length ? $scope.query.orgs : $scope.organisations;
        return RisarApi.search_event.lpu_doctors_list(orgs)
        .then(function (result) {
            $scope.doctors = default_docs.concat(result);
            setFltDoctor();
        });
    };

    $scope.reset_filters = function () {
        $scope.query = {
            areas: [],
            orgs: [],
            checkup_date_from: null,
            checkup_date_to: null,
            bdate_from: null,
            bdate_to: null,
            risk: [],
            radz_risk: [],
            closed: $scope.closed_items[0],
            client_work_group: {},
            fertilization_type: {},
            age_min: null,
            age_max: null,
            request_types: [],
            person: $scope.query.person,
            curators: $scope.query.curators,
            preg_week_min: null,
            preg_week_max: null,
            latest_inspection_gt: null,
            pathology: [],
            risk_groups: [],
            epicrisis_delivery_date_gt: null,
            card_fill: $scope.card_fill_rate[0],
            card_section: $scope.card_sections[0],
            mkbs: [],
            closed_diags: null,
            overdue: null,
            measure_type: $scope.rbMeasureType.objects[0],
            controlled_events: null,
            missed_last_checkup: null
        };
        return $scope.refresh_areas();
    };
    var areas_promise = $scope.reset_filters();
    var tc = new TimeoutCallback(perform, 600);

    $scope.perform = function () {
        tc.start();
    };
    $scope.onPageChanged = function () {
        perform(true);
    };
    $scope.canChangeDoctor = function () {
        return CurrentUser.current_role_in('admin', 'overseer1', 'overseer2', 'overseer3') ||
            WMConfig.local_config.risar.extended_search.common_access_doctor;
    };
    $scope.canChangeCurator = function () {
        return CurrentUser.current_role_in('admin', 'overseer1', 'overseer2', 'overseer3') ||
            WMConfig.local_config.risar.extended_search.common_access_curator;
    };
    $scope.isCurator = function () {
        return CurrentUser.current_role_in('overseer1', 'overseer2', 'overseer3');
    };
    $scope.isCardSectionDisabled = function () {
        if ($scope.query.card_fill == $scope.card_fill_rate[0]) {
            $scope.query.card_section = $scope.card_sections[0];
            return true;
        }
        return false;
    };
    $scope.isMeasureTypeDisabled = function () {
        return !$scope.query.overdue;
    };
    $scope.filterForPregCardsAvailable = function () {
        return $scope.query.request_types.some(function (rt) {
            return rt.code === 'pregnancy';
        });
    };

    var setFltDoctor = function () {
        if (CurrentUser.current_role_in('admin', 'obstetrician')) {
           var doc_id = CurrentUser.get_main_user().id,
                person_idx = _.findIndex($scope.doctors, function (doctor) {
                    return doctor.id === doc_id;
                });
            if (person_idx !== -1) {
                $scope.query.person = $scope.doctors[person_idx];
            }
        } else {
            $scope.query.person = default_docs[0];
        }
    };
    var setFltCurators = function () {
        if (CurrentUser.current_role_in('overseer1', 'overseer2', 'overseer3')) {
            var cur_id = CurrentUser.get_main_user().id,
                curators_list = [],
                cur_role_code = CurrentUser.current_role.substr(-1);
            for (var i = 0; i < $scope.curators.length; i++) {
                if ($scope.curators[i].person_id === cur_id &&
                        $scope.curators[i].level_code === cur_role_code) {
                    curators_list.push($scope.curators[i]);
                }
            }
            if (curators_list.length) {
                $scope.query.curators = curators_list;
            }
        } else {
            $scope.query.curators = [];
        }
    };
    var setFilterFromArgs = function (args) {
        if (args.hasOwnProperty('request_type')) {
            $scope.query.request_types = $scope.request_types.filter(function (rt) {
                return rt.code === args.request_type;
            });
        }
        if (args.hasOwnProperty('person_id')) {
            args.person_id = parseInt(args.person_id);
            var new_person = $scope.doctors.filter(function (d) {
                return d.id === args.person_id;
            })[0];
            if (new_person) $scope.query.person = new_person;
        }
        if (args.hasOwnProperty('closed')) {
            args.closed = args.closed === 'false' ? false : args.closed === 'true' ? true : undefined;
            var new_closed_status = $scope.closed_items.filter(function (cl) {
                return cl.value === args.closed;
            })[0];
            if (new_closed_status) $scope.query.closed = new_closed_status;
        }
        if (args.hasOwnProperty('preg_week_min')) {
            $scope.query.preg_week_min = parseInt(args.preg_week_min);
        }
        if (args.hasOwnProperty('preg_week_max')) {
            $scope.query.preg_week_max = parseInt(args.preg_week_max);
        }
        if (args.hasOwnProperty('latest_inspection_gt')) {
            $scope.query.latest_inspection_gt = parseInt(args.latest_inspection_gt);
        }
        if (args.hasOwnProperty('risk_rate')) {
            $scope.query.risk = $scope.risks_rb.objects.filter(function (rr) {
                return rr.code === args.risk_rate;
            });
        }
        if (args.hasOwnProperty('radz_risk_rate')) {
            $scope.query.radz_risk = $scope.radz_risks_rb.objects.filter(function (rr) {
                return rr.code === args.radz_risk_rate;
            });
        }
        if (args.hasOwnProperty('pathology_id')) {
            var new_pathology = $scope.pathology_rb.get(args.pathology_id);
            if (new_pathology) $scope.query.pathology = [new_pathology];
        }
        if (args.hasOwnProperty('risk_group')) {
            $scope.query.risk_groups = $scope.rbRisarRiskGroup.objects.filter(function (rg) {
                return rg.code === args.risk_group;
            });
        }
        if (args.hasOwnProperty('epicrisis_delivery_date_gt')) {
            $scope.query.epicrisis_delivery_date_gt = parseInt(args.epicrisis_delivery_date_gt);
        }
        if (args.hasOwnProperty('card_fill_opt')) {
            var card_fill_opt = parseInt(args.card_fill_opt);
            $scope.query.card_fill = $scope.card_fill_rate[card_fill_opt];
        }
        if (args.hasOwnProperty('card_section_opt')) {
            var card_section_opt = parseInt(args.card_section_opt);
            $scope.query.card_section = $scope.card_sections[card_section_opt];
        }
        if (args.hasOwnProperty('org_id')) {
            var organization = $scope.organisations.filter(function (organization) {
                return organization.id == args.org_id;
            })[0];
            $scope.query.orgs = organization ? [organization] : [];
        }
        if (args.hasOwnProperty('controlled_events')) {
            $scope.query.controlled_events = args.controlled_events === 'false' ?
                false :
                args.controlled_events === 'true' ?
                    true :
                    undefined;
        }
        if (args.hasOwnProperty('missed_last_checkup')) {
            $scope.query.missed_last_checkup = args.missed_last_checkup === 'false' ?
                false :
                args.missed_last_checkup === 'true' ?
                    true :
                    undefined;
        }
    };

    // start
    $q.all([areas_promise, $scope.risks_rb.loading, $scope.radz_risks_rb.loading, $scope.pathology_rb.loading,
            $scope.rbRisarRiskGroup.loading, $scope.rbMeasureType.loading]).then(function () {
        setFltDoctor();
        setFltCurators();
        setFilterFromArgs(aux.getQueryParams(window.location.search));

        $scope.$watchCollection('query', function () {
            tc.start()
        });
        $scope.$watchCollection('query.risk', function () {
            tc.start()
        });
        $scope.$watchCollection('query.radz_risk', function () {
            tc.start()
        });
        $scope.$watchCollection('query.request_types', function (n, o_) {
            tc.start()
            $scope.isPregnancy= _.pluck(n, 'code').indexOf('pregnancy')>-1;
        });
        $scope.$watchCollection('query.pathology', function () {
            tc.start()
        });
        var empty_measure = {
            id: 0,
            name: 'Любой тип',
            code: 'any'
        };
        $scope.rbMeasureType.objects.unshift(empty_measure);
        $scope.query.measure_type = $scope.rbMeasureType.objects[0];
    });
};

WebMis20.controller('EventSearchCtrl', ['$scope', '$q', 'RisarApi', 'TimeoutCallback', 'RefBookService', 'CurrentUser',
    'WMConfig',
    EventSearchCtrl]);