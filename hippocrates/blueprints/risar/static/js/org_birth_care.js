'use strict';

var OrgBirthCareCtrl = function ($scope, RisarApi) {
    $scope.selected = {
        obcl_id: null
    };
    $scope.isLevelSelected = function (obcl_id) {
        return $scope.selected.obcl_id === obcl_id;
    };
    $scope.init = function () {
        RisarApi.desktop.get_info().
            then(function (data) {
                $scope.obcl_items = data.obcl_items;
                if ($scope.obcl_items.length) {
                    $scope.selectOBCL($scope.obcl_items[0]);
                }
            });
    };
    $scope.selectOBCL = function (obcl) {
        $scope.selected.obcl_id = obcl.id;
        RisarApi.curation.get_org_patient_count(obcl.id).
            then(function (data) {
                $scope.org_items = data.org_items;
            });
    };

    $scope.init();
};

WebMis20.controller('OrgBirthCareCtrl', ['$scope', 'RisarApi',
    OrgBirthCareCtrl]);