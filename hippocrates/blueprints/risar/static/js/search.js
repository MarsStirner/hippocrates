/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventSearchCtrl = function ($scope, $q, RisarApi, TimeoutCallback, RefBookService, CurrentUser) {
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
    $scope.rbRequestType = RefBookService.get('rbRequestType');
    $scope.request_types = [];
    $scope.$watchCollection('rbRequestType.objects', function (n, o) {
        if (!_.isArray(n) || _.isEqual(n, o)) return;
        $scope.request_types = _.filter(n, function (i) {
            return _.contains(['gynecological', 'pregnancy'], i.code)
        })
    });

    $scope.risks_rb = RefBookService.get('PerinatalRiskRate');

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
        closed: $scope.closed_items[0],
        client_work_group: {},
        age_min: null,
        age_max: null,
        request_types: [],
        preg_week_min: null,
        preg_week_max: null,
        latest_inspection_gt: null
    };

    $scope.get_search_data = function () {
        var orgs = [];
        var from_orgs = $scope.query.orgs.length ? $scope.query.orgs: $scope.organisations;
        from_orgs.forEach(function(i) {if(i.id) orgs.push(i.id);});
        return {
            page: $scope.pager.current_page,
            areas: $scope.query.areas,
            curators: $scope.query.curators,
            org_ids: orgs,
            doc_id: $scope.query.person.id,
            fio: $scope.query.fio || undefined,
            checkup_date_from: $scope.query.checkup_date_from || undefined,
            checkup_date_to: $scope.query.checkup_date_to || undefined,
            bdate_from: $scope.query.bdate_from || undefined,
            bdate_to: $scope.query.bdate_to || undefined,
            risk: _.pluck($scope.query.risk, 'id') || undefined,
            closed: $scope.query.closed.value,
            client_workgroup: $scope.query.client_workgroup || undefined,
            age_max: $scope.query.age_max || undefined,
            age_min: $scope.query.age_min || undefined,
            request_types: _.pluck($scope.query.request_types, 'id') || undefined,
            preg_week_min: $scope.query.preg_week_min || undefined,
            preg_week_max: $scope.query.preg_week_max || undefined,
            latest_inspection_gt: (
                _.isNumber($scope.query.latest_inspection_gt) &&
                $scope.query.latest_inspection_gt >= 1 &&
                $scope.query.latest_inspection_gt <= 500
            ) ? $scope.query.latest_inspection_gt : undefined
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
            closed: $scope.closed_items[0],
            client_work_group: {},
            age_min: null,
            age_max: null,
            request_types: [],
            person: $scope.query.person,
            curators: $scope.query.curators,
            preg_week_min: null,
            preg_week_max: null,
            latest_inspection_gt: null
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
        return CurrentUser.current_role_in('admin');
    };
    $scope.canChangeCurator = function () {
        return CurrentUser.current_role_in('admin');
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
                curators_list = [];
            for (var i = 0; i < $scope.curators.length; i++) {
                if ($scope.curators[i].person_id === cur_id) {
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
        if (args.hasOwnProperty('person_id') && $scope.canChangeDoctor()) {
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
    };

    // start
    $q.all([areas_promise, $scope.risks_rb.loading]).then(function () {
        setFltDoctor();
        setFltCurators();
        setFilterFromArgs(aux.getQueryParams(window.location.search));

        $scope.$watchCollection('query', function () {
            tc.start()
        });
        $scope.$watchCollection('query.risk', function () {
            tc.start()
        });
        $scope.$watchCollection('query.request_types', function () {
            tc.start()
        });
    });
};

WebMis20.controller('EventSearchCtrl', ['$scope', '$q', 'RisarApi', 'TimeoutCallback', 'RefBookService', 'CurrentUser',
    EventSearchCtrl]);