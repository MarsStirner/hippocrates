'use strict';

var OrgBirthCareCtrl = function ($scope, RisarApi) {
    $scope.selected = {
        obcl_id: null
    };
    $scope.isLevelSelected = function (obcl_id) {
        return $scope.selected.obcl_id === obcl_id;
    };
    $scope.init = function () {
        RisarApi.stats.get_obcl_info().
            then(function (data) {
                $scope.obcl_items = data.obcl_items;
                $scope.empty_obcl = data.empty_obcl;
                if ($scope.obcl_items.length) {
                    $scope.selectOBCL($scope.obcl_items[0]);
                }
            });
    };
    $scope.selectOBCL = function (obcl) {
        $scope.selected.obcl_id = obcl.id;
        RisarApi.stats.get_obcl_org_info(obcl.id).
            then(function (data) {
                $scope.org_items = data.org_items;
            });
    };
    $scope.selectEmptyOBCL = function () {
        $scope.selectOBCL({
            id: undefined
        });
    };
    $scope.getRRToolTipText = function (riskRate) {
        var text = 'Количество пациенток {0} степени перинатального риска, планово установленных на родоразрешение';
        var rrText = '';
        if (riskRate.code === 'high') rrText = 'высокой';
        else if (riskRate.code === 'medium') rrText = 'средней';
        else if (riskRate.code === 'low') rrText = 'низкой';
        else rrText = 'неопределенной';
        return text.format(rrText);
    };

    $scope.init();
};
var OrgBirthCareViewCtrl = function ($scope, RisarApi) {
    $scope.getRRToolTipText = function (riskRate) {
        var text = 'Количество пациенток {0} степени перинатального риска, планово установленных на родоразрешение';
        var rrText = '';
        if (riskRate.code === 'high') rrText = 'высокой';
        else if (riskRate.code === 'medium') rrText = 'средней';
        else if (riskRate.code === 'low') rrText = 'низкой';
        else rrText = 'неопределенной';
        return text.format(rrText);
    };
    RisarApi.stats.get_obcl_info().
        then(function (data) {
            $scope.obcl_items = data.obcl_items;
        });
};


WebMis20.controller('OrgBirthCareCtrl', ['$scope', 'RisarApi',
    OrgBirthCareCtrl]);
WebMis20.controller('OrgBirthCareViewCtrl', ['$scope', 'RisarApi',
    OrgBirthCareViewCtrl]);