'use strict';

var PregnancyWeekDistributionCtrl = function ($scope, RisarApi, CurrentUser) {
    var person_id = CurrentUser.id;
    $scope.curation_level_code = $scope.curation_level.code; // from parent ctrl
    $scope.stats_data = {};
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

    $scope.init = function () {
        $scope.refresh_data();
    };

    $scope.init();
};


WebMis20.controller('PregnancyWeekDistributionCtrl', ['$scope', 'RisarApi', 'CurrentUser',
    PregnancyWeekDistributionCtrl]);