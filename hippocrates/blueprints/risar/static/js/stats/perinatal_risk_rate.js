'use strict';

var PerinatalRiskRateViewCtrl = function ($scope, RisarApi, RefBookService) {
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl

    $scope.slices = [];
    $scope.slices_x = function (d) {
        return d.key;
    };
    $scope.slices_y = function (d) {
        return d.value;
    };
    $scope.slices_c = function (d, i) {
        // А это, ребятки, костыль, потому что где-то в d3 или nv - багулечка
        return d.data.color;
    };
    $scope.PregnancyPathology = undefined;
    $scope.preg_pathg_stats = {};

    $scope.refresh_data = function () {
        RisarApi.stats.get_perinatal_risk_info($scope.curation_level_code)
            .then(function (result) {
                $scope.slices = [];
                if (result['1']) {
                    $scope.slices.push({
                        key: 'Не определена',
                        value: result['1'],
                        color: '#707070'
                    })
                }
                if (result['2']) {
                    $scope.slices.push({
                        key: 'Низкая',
                        value: result['2'],
                        color: '#30D040'
                    })
                }
                if (result['3']) {
                    $scope.slices.push({
                        key: 'Средняя',
                        value: result['3'],
                        color: '#f39c12'
                    })
                }
                if (result['4']) {
                    $scope.slices.push({
                        key: 'Высокая',
                        value: result['4'],
                        color: '#dd4b39'
                    })
                }
            });
        RisarApi.stats.get_pregnancy_pathology_info($scope.curation_level_code)
            .then(function (data) {
                $scope.preg_pathg_stats = data.preg_pathg_stats;
            });
    };
    $scope.init = function () {
        $scope.PregnancyPathology = RefBookService.get('PregnancyPathology');
        $scope.refresh_data();
    };
    $scope.flt_pp = function (pp) {
        return pp.code !== 'undefined';
    };
    $scope.getPregPathgPct = function (pp_code) {
        return _.isEmpty($scope.preg_pathg_stats) ? null : '{0} %'.format($scope.preg_pathg_stats[pp_code].pct);
    };

    $scope.init();
};


WebMis20.controller('PerinatalRiskRateViewCtrl', ['$scope', 'RisarApi', 'RefBookService',
    PerinatalRiskRateViewCtrl]);