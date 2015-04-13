/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, $modal, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var event_id = params.event_id;
    $scope.has_desease = function(has_diag){
        if ($scope.chart){
            if (has_diag){
                return 'Положительно'
            } else if ($scope.chart.checkups.length){
                return 'Отрицательно'
            }
        }
        return 'Нет данных'
    }

    $scope.declOfNum = function (number, titles)
    {
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    }

    var reload_chart = function () {
        RisarApi.chart.get(event_id, ticket_id)
        .then(function (event) {
            $scope.chart = event;
            var mother_anamnesis = $scope.chart.anamnesis.mother;
            $scope.first_checkup = $scope.chart.checkups[$scope.chart.checkups.length-1];
            if ($scope.chart.pregnancy_week > 40) {
                $scope.pregnancy_week = '40+'}
            else {
                $scope.pregnancy_week = $scope.chart.pregnancy_week
            }
            $scope.chart.bad_habits_mother = [{value:mother_anamnesis ? mother_anamnesis.alcohol: false, text: 'алкоголь'},
                {value:mother_anamnesis ? mother_anamnesis.smoking: false, text: 'курение'},
                {value:mother_anamnesis ? mother_anamnesis.toxic: false, text: 'токсические вечества'},
                {value:mother_anamnesis ? mother_anamnesis.drugs: false,text: 'наркотики'}];

            function get_mass_gain(prev, curr, i){
                if (i === $scope.chart.checkups.length - 1) {
                    curr.weight_gain = [0, 0];
                }
                var num_days = moment(prev.beg_date).diff(moment(curr.beg_date), 'days');
                prev.weight_gain = curr.weight ? [prev.weight - curr.weight, num_days ] : [0, num_days];
                return curr
            }
            $scope.chart.checkups.reduce(get_mass_gain, [{}]);
//            $scope.chart.bad_habits_father = [{value:$scope.chart.anamnesis.father.alcohol, text: 'алкоголь'},
//                {value:$scope.chart.anamnesis.father.smoking, text: 'курение'},
//                {value:$scope.chart.anamnesis.father.toxic, text: 'токсические вечества'},
//                {value:$scope.chart.anamnesis.father.drugs,text: 'наркотики'}];
        })
    };
    reload_chart();
};
