'use strict';

var PregnancyWeekDistributionCtrl = function ($scope, RisarApi, CurrentUser, RefBookService) {
    var person_id = CurrentUser.id,
        div3;
    $scope.rbRisarRiskGroup = RefBookService.get('rbRisarRiskGroup');
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.stats_data = {};
    $scope.risks_data = {};
    $scope.risks_layouting = [];
    $scope.diagram_data = [{
        key: "Пациентки по сроку беременности",
        values: $scope.stats_data
    }];

    $scope.refresh_data = function () {
        RisarApi.stats.get_pregnancy_week_diagram(person_id, $scope.curation_level_code).
            then(function (data) {
                $scope.stats_data = data;
                $scope.diagram_data = [{
                    key: "Пациентки по сроку беременности",
                    values: $scope.stats_data.preg_week_distribution
                }];
            });
        RisarApi.stats.get_risk_group_distribution(person_id, $scope.curation_level_code)
            .then(function (data) {
                $scope.risks_data = data;
                var l = $scope.risks_layouting = [[], [], []];
                _.chain(data)
                    .pairs()
                    .tap(function (list) {
                        div3 = Math.ceil(list.length / 3) || 1;
                    })
                    .sortBy(function (pair) {
                        return pair[0]
                    })
                    .each(function (item, index, context) {
                        l[Math.floor(index / div3)].push(item[0]);
                    })
            })
    };
    $scope.toolTipContent_pregnancy_week = function(){
        return function(key, x, y, e, graph) {
            return  '<h4>'+ x  + ' неделя'+ '</h4>'+ '<p>' +  y + '</p>'
        }
    };
    $scope.colorFunction = function() {
        return function(d, i) {
            if (d[0]<=14){
                return '#F493F2'
            } else if (14 < d[0] && d[0]<= 26){
                return '#E400E0'
            } else if (27 <= d[0] && d[0]<= 40){
                return '#9600CD'
            } else {
                return '#5416B4';
            }
        };
    };
    $scope.yAxisTickFormat = function(d) {
        return d;
    };

    $scope.$on('elementClick.directive', function(angularEvent, event){
        $scope.openExtendedSearchFromDiagram(event);
    });
    $scope.openExtendedSearchFromDiagram = function (event) {
        var pw = parseInt(event.point[0]),
            mouse_button = event.e.button;  // 0-left, 1-middle
        var args = {
            request_type: 'pregnancy',
            person_id: CurrentUser.get_main_user().id,
            closed: false,
            preg_week_min: pw,
            preg_week_max: pw
        };
        RisarApi.search_event.openExtendedSearch(args, mouse_button === 1)
    };

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('PregnancyWeekDistributionCtrl', ['$scope', 'RisarApi', 'CurrentUser', 'RefBookService',
    PregnancyWeekDistributionCtrl]);