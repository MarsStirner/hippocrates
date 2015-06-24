/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, $modal, RisarApi, PrintingService, PrintingDialog) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var event_id = params.event_id;
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar_talon");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.chart.id
        }
    };
    $scope.has_desease = function(has_diag){
        if ($scope.chart){
            if (has_diag){
                return 'Положительно'
            } else if ($scope.chart.checkups.length){
                return 'Отрицательно'
            }
        }
        return 'Нет данных'
    };

    var reload_chart = function () {
        if (!ticket_id) {
            RisarApi.chart.get_header(event_id).
                then(function (data) {
                    $scope.header = data.header;
                });
        }
        RisarApi.chart.get(event_id, ticket_id)
            .then(function (event) {
                $scope.chart = event;
                var mother_anamnesis = $scope.chart.anamnesis.mother;
                $scope.chart.bad_habits_mother = [{value:mother_anamnesis ? mother_anamnesis.alcohol: false, text: 'алкоголь'},
                    {value:mother_anamnesis ? mother_anamnesis.smoking: false, text: 'курение'},
                    {value:mother_anamnesis ? mother_anamnesis.toxic: false, text: 'токсические вечества'},
                    {value:mother_anamnesis ? mother_anamnesis.drugs: false,text: 'наркотики'}];
                //$scope.chart.bad_habits_father = [{value:$scope.chart.anamnesis.father.alcohol, text: 'алкоголь'},
                //    {value:$scope.chart.anamnesis.father.smoking, text: 'курение'},
                //    {value:$scope.chart.anamnesis.father.toxic, text: 'токсические вечества'},
                //    {value:$scope.chart.anamnesis.father.drugs,text: 'наркотики'}];

                if (ticket_id) {
                    RisarApi.chart.get_header($scope.chart.id).
                        then(function (data) {
                            $scope.header = data.header;
                        });
                }
            });
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
    reload_chart();
};

var InspectionViewCtrl = function ($scope, $modal, RisarApi, PrintingService, PrintingDialog) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar_talon");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.chart.id
        }
    };
    $scope.declOfNum = function (number, titles) {
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    };

    var reload = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.checkup.get_list(event_id)
            .then(function (data) {
                $scope.checkups = data.checkups;

                // calculate mass gain
                $scope.first_checkup = $scope.checkups.length ? $scope.checkups[0] : null;
                function get_mass_gain(prev, curr, i){
                    if (i === 0) {
                        curr.weight_gain = [0, 0];
                    }
                    var num_days = moment(curr.beg_date).diff(moment(prev.beg_date), 'days');
                    curr.weight_gain = prev.weight ? [curr.weight - prev.weight, num_days ] : [0, num_days];
                    return curr
                }
                $scope.checkups.reduce(get_mass_gain, [{}]);
            });
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()){
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
    reload();
};

WebMis20.controller('ChartCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog',
    ChartCtrl]);
WebMis20.controller('InspectionViewCtrl', ['$scope', '$modal', 'RisarApi', 'PrintingService', 'PrintingDialog',
    InspectionViewCtrl]);