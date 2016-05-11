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
    $scope.results = [];
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
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
            risk: get_risk_list(), //$scope.query.risk.id,
            closed: $scope.query.closed.value
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
            $scope.query.curators = [];
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
            $scope.query.person = $scope.doctors[0];
        });
    };
    $scope.risks_rb = RefBookService.get('PerinatalRiskRate');

    $scope.reset_filters = function () {
        $scope.query = {
            areas: [],
            curators: [],
            orgs: [],
            person: default_docs[0],
            checkup_date_from: null,
            checkup_date_to: null,
            bdate_from: null,
            bdate_to: null,
            risk: [],
            closed: $scope.closed_items[0]
        };
        return $scope.refresh_areas();
    };
    var areas_promise = $scope.reset_filters();
    var tc = new TimeoutCallback(perform, 600);

    $scope.perform = function () {
        tc.start();
    };
    function get_risk_list () {
        if ($scope.query.risk.length) {
            return _.pluck($scope.query.risk, 'id')
        }
    }
    $scope.onPageChanged = function () {
        perform(true);
    };

    // start
    $q.all([areas_promise]).then(function () {
        var doc_id = CurrentUser.get_main_user().id,
            person_idx = _.findIndex($scope.doctors, function (doctor) {
                return doctor.id === doc_id;
            });
        $scope.query.person = $scope.doctors[person_idx !== -1 ? person_idx : 0];

        $scope.$watchCollection('query', function () {
            tc.start()
        });
        $scope.$watchCollection('query.risk', function () {
            tc.start()
        });
    });
};

WebMis20.controller('EventSearchCtrl', ['$scope', '$q', 'RisarApi', 'TimeoutCallback', 'RefBookService', 'CurrentUser',
    EventSearchCtrl]);