/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventSearchCtrl = function ($scope, RisarApi, TimeoutCallback, RefBookService) {
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
    $scope.query = {
        org: default_orgs[0],
        person: default_docs[0],
        checkup_date: null,
        bdate: null,
        risk: [],
        closed: $scope.closed_items[0]
    };
    $scope.results = [];
    var perform = function () {
        var data = {
            org_id: $scope.query.org.id,
            doc_id: $scope.query.person.id,
            fio: $scope.query.fio || undefined,
            checkup_date: $scope.query.checkup_date || undefined,
            bdate: $scope.query.bdate || undefined,
            risk: get_risk_list(), //$scope.query.risk.id,
            closed: $scope.query.closed.value
        };
        console.log(JSON.stringify($scope.query));
        console.log(JSON.stringify(data));
        RisarApi.search_event.get(data).then(function (result) {
            $scope.results = result;
        })
    };
    $scope.refresh_organisations = function () {
        RisarApi.search_event.lpu_list()
        .then(function (result) {
            $scope.organisations = default_orgs.concat(result);
            $scope.refresh_doctors();
        })
    };
    $scope.refresh_doctors = function () {
        RisarApi.search_event.lpu_doctors_list($scope.query.org.id)
        .then(function (result) {
            $scope.doctors = default_docs.concat(result);
            $scope.query.person = default_docs[0];
        })
    };
    $scope.risks_rb = RefBookService.get('PrenatalRiskRate');

    $scope.refresh_organisations();

    var tc = new TimeoutCallback(perform, 600);

    $scope.perform = function () {
        tc.start();
    };
    function get_risk_list () {
        if ($scope.query.risk.length) {
            return _.pluck($scope.query.risk, 'id')
        }
    }

    $scope.$watchCollection('query', function () {
        tc.start()
    });
    $scope.$watchCollection('query.risk', function () {
        tc.start()
    });
};
