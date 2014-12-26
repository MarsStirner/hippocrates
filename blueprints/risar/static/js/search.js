/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventSearchCtrl = function ($scope, RisarApi, TimeoutCallback) {
    var default_orgs = [{
        full_name: 'Все',
        short_name: 'Все'
    }];
    var default_docs = [{
        full_name: 'Все',
        name: 'Все'
    }];
    $scope.query = {
        org: default_orgs[0],
        person: default_docs[0]
    };
    $scope.results = [];
    var perform = function () {
        RisarApi.search_event.get({
            org_id: $scope.query.org.id,
            doc_id: $scope.query.person.id,
            fio: $scope.query.fio || undefined
        }).then(function (result) {
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
            perform();
        })
    };

    $scope.refresh_organisations();

    var tc = new TimeoutCallback(perform, 600);

    $scope.perform = function () {
        tc.start();
    }
};
