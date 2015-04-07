/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventSearchCtrl = function ($scope, $q, RisarApi, TimeoutCallback, RefBookService, CurrentUser) {
    var default_orgs = [{
        full_name: 'Все',
        short_name: 'Все'
    }];
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
    $scope.reset_filters = function () {
        $scope.query = {
            org: default_orgs[0],
            person: default_docs[0],
            checkup_date_from: null,
            checkup_date_to: null,
            bdate_from: null,
            bdate_to: null,
            risk: [],
            closed: $scope.closed_items[0]
        };
    };
    $scope.reset_filters();
    $scope.results = [];
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
    };

    var perform = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var data = {
            page: $scope.pager.current_page,
            org_id: $scope.query.org.id,
            doc_id: $scope.query.person.id,
            fio: $scope.query.fio || undefined,
            checkup_date_from: $scope.query.checkup_date_from || undefined,
            checkup_date_to: $scope.query.checkup_date_to || undefined,
            bdate_from: $scope.query.bdate_from || undefined,
            bdate_to: $scope.query.bdate_to || undefined,
            risk: get_risk_list(), //$scope.query.risk.id,
            closed: $scope.query.closed.value
        };
        //console.log(JSON.stringify($scope.query));
        //console.log(JSON.stringify(data));
        RisarApi.search_event.get(data).then(function (result) {
            $scope.pager.pages = result.total_pages;
            $scope.pager.record_count = result.count;
            $scope.results = result.events;
        });
    };
    $scope.refresh_organisations = function () {
        return RisarApi.search_event.lpu_list()
        .then(function (result) {
            $scope.organisations = default_orgs.concat(result);
            return $scope.refresh_doctors();
        });
    };
    $scope.refresh_doctors = function () {
        return RisarApi.search_event.lpu_doctors_list($scope.query.org.id)
        .then(function (result) {
            $scope.doctors = default_docs.concat(result);
            var doc_id = CurrentUser.get_main_user().id,
                person_idx = _.findIndex($scope.doctors, function (doctor) {
                    return doctor.id === doc_id;
                });
            $scope.query.person = $scope.doctors[person_idx !== -1 ? person_idx : 0];
        });
    };
    $scope.risks_rb = RefBookService.get('PrenatalRiskRate');

    var org_promise = $scope.refresh_organisations();

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
    $q.all([org_promise]).then(function () {
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