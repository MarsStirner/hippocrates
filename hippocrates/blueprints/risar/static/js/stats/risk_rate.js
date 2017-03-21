'use strict';

var RiskRateViewCtrl = function ($scope, $q, RisarApi, RefBookService, CurrentUser) {
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl

    $scope.slices = [];
    $scope.slices_radz = [];
    $scope.slices_regional = [];
    var regional_rr_colors = {
        1: '#30D040', // low
        2: '#f39c12', // middle
        3: '#dd4b39' // high
    };
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
                        color: '#707070',
                        risk_rate: $scope.PerinatalRiskRate.get(1)
                    })
                }
                if (result['2']) {
                    $scope.slices.push({
                        key: 'Низкая',
                        value: result['2'],
                        color: '#30D040',
                        risk_rate: $scope.PerinatalRiskRate.get(2)
                    })
                }
                if (result['3']) {
                    $scope.slices.push({
                        key: 'Средняя',
                        value: result['3'],
                        color: '#f39c12',
                        risk_rate: $scope.PerinatalRiskRate.get(3)
                    })
                }
                if (result['4']) {
                    $scope.slices.push({
                        key: 'Высокая',
                        value: result['4'],
                        color: '#dd4b39',
                        risk_rate: $scope.PerinatalRiskRate.get(4)
                    })
                }
            });
        RisarApi.stats.get_pregnancy_pathology_info($scope.curation_level_code)
            .then(function (data) {
                $scope.preg_pathg_stats = data.preg_pathg_stats;
            });
        RisarApi.stats.get_radz_risk_info($scope.curation_level_code).then(function (result) {
                $scope.slices_radz = [];
                if (result['low']) {
                    $scope.slices_radz.push({
                        key: 'Низкая',
                        value: result['low'],
                        color: '#30D040',
                        radz_risk_rate: $scope.RadzinskyRiskRate.get(1)
                    })
                }
                if (result['medium']) {
                    $scope.slices_radz.push({
                        key: 'Средняя',
                        value: result['medium'],
                        color: '#f39c12',
                        radz_risk_rate: $scope.RadzinskyRiskRate.get(2)
                    })
                }
                if (result['high']) {
                    $scope.slices_radz.push({
                        key: 'Высокая',
                        value: result['high'],
                        color: '#dd4b39',
                        radz_risk_rate: $scope.RadzinskyRiskRate.get(3)
                    })
                }
            });
        RisarApi.stats.get_regional_risk_info($scope.curation_level_code)
            .then(function (result) {
                $scope.slices_regional = [];
                var cur_rr;
                for (var rr_code in result) {
                    if (result.hasOwnProperty(rr_code)) {
                        cur_rr = $scope.rbRisarRegionalRiskRate.get_by_code(rr_code);
                        $scope.slices_regional.push({
                            key: cur_rr.name,
                            value: result[rr_code],
                            color: regional_rr_colors[cur_rr.id] || 'cyan',
                            regional_risk_rate: cur_rr
                        });
                    }
                }
            });
    };

    $scope.$on('elementClick.directive', function (angularEvent, event) {
        $scope.openExtendedSearchFromDiagram(event);
    });
    var getDiagramRateName = function (diagram_point) {
        if (diagram_point.hasOwnProperty('risk_rate')) return 'risk_rate';
        else if (diagram_point.hasOwnProperty('radz_risk_rate')) return 'radz_risk_rate';
        else if (diagram_point.hasOwnProperty('regional_risk_rate')) return 'regional_risk_rate';
        return undefined;
    };
    $scope.openExtendedSearchFromDiagram = function (event) {
        var risk_rate_name = getDiagramRateName(event.point);
        var rr = event.point[risk_rate_name]
        if (rr !== undefined) {
            var mouse_button = event.pos.button;  // 0-left, 1-middle
            var args = {
                request_type: 'pregnancy',
                closed: false
            };
            args[risk_rate_name] = rr.code;
            if (!$scope.curation_level_code) {
                args.person_id = CurrentUser.get_main_user().id;
            }
            RisarApi.search_event.openExtendedSearch(args, mouse_button === 1)
        }
    };

    $scope.flt_pp = function (pp) {
        return pp.code !== 'undefined';
    };
    $scope.getPregPathgCount = function (pp_code) {
        return _.isEmpty($scope.preg_pathg_stats) ? null : '{0}'.format($scope.preg_pathg_stats[pp_code].count);
    };
    $scope.getPregPathgPct = function (pp_code) {
        return _.isEmpty($scope.preg_pathg_stats) ? null : '{0}%'.format($scope.preg_pathg_stats[pp_code].pct);
    };
    $scope.getExtendedSearchUrl = function (pathology_id) {
        var args = {
            request_type: 'pregnancy',
            closed: false,
            pathology_id: pathology_id
        };
        if (!$scope.curation_level_code) {
            args.person_id = CurrentUser.get_main_user().id;
        }
        return RisarApi.search_event.getExtendedSearchUrl(args);
    };

    $scope.init = function () {
        $scope.PregnancyPathology = RefBookService.get('PregnancyPathology');
        $scope.PerinatalRiskRate = RefBookService.get('PerinatalRiskRate');
        $scope.RadzinskyRiskRate = RefBookService.get('RadzinskyRiskRate');
        $scope.rbRisarRegionalRiskRate = RefBookService.get('rbRisarRegionalRiskRate');

        $q.all(
            $scope.PregnancyPathology.loading, $scope.PerinatalRiskRate.loading,
            $scope.rbRisarRegionalRiskRate.loading
        ).then($scope.refresh_data);
    };

    $scope.init();
};


WebMis20.controller('RiskRateViewCtrl', ['$scope', '$q', 'RisarApi', 'RefBookService', 'CurrentUser', RiskRateViewCtrl]);