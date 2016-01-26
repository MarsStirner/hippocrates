'use strict';

var OrgCurationCtrl = function ($scope, RisarApi, RefBookService) {
    $scope.hasCurators = function (org, level) {
        return org.curations.hasOwnProperty(level.id);
    };
    $scope.getOrgCurators = function (org, level) {
        return org.curations[level.id];
    };
    $scope.init = function () {
        $scope.rbOrgCurationLevel = RefBookService.get('rbOrgCurationLevel');
        RisarApi.stats.get_org_curation_info().
            then(function (data) {
                $scope.rbOrgCurationLevel.loading.then(function () {
                    $scope.orgs = data.orgs;
                });
            });
    };

    $scope.init();
};

WebMis20.controller('OrgCurationCtrl', ['$scope', 'RisarApi', 'RefBookService',
    OrgCurationCtrl]);