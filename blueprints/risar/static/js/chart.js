/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var ChartCtrl = function ($scope, $modal, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var ticket_id = params.ticket_id;
    var event_id = params.event_id;
    var reload_chart = function () {
        RisarApi.chart.get(event_id, ticket_id)
        .then(function (event) {
            $scope.chart = event;
            if ($scope.chart.pregnancy_week > 40) {
                $scope.pregnancy_week = '40+'}
            else {
                $scope.pregnancy_week = $scope.chart.pregnancy_week
            }
            var mld = safe_traverse(event, ['anamnesis','mother','menstruation_last_date']);
            if (mld){
                $scope.birth_date = moment(mld).add(280, 'days').format("DD.MM.YYYY");
            }
            $scope.chart.bad_habits_mother = [{value:$scope.chart.anamnesis.mother.alcohol, text: 'алкоголь'},
                {value:$scope.chart.anamnesis.mother.smoking, text: 'курение'},
                {value:$scope.chart.anamnesis.mother.toxic, text: 'токсические вечества'},
                {value:$scope.chart.anamnesis.mother.drugs,text: 'наркотики'}];
//            $scope.chart.bad_habits_father = [{value:$scope.chart.anamnesis.father.alcohol, text: 'алкоголь'},
//                {value:$scope.chart.anamnesis.father.smoking, text: 'курение'},
//                {value:$scope.chart.anamnesis.father.toxic, text: 'токсические вечества'},
//                {value:$scope.chart.anamnesis.father.drugs,text: 'наркотики'}];
        })
    };
    var open_attach_lpu_edit = function () {
        var scope = $scope.$new();
        scope.model = $scope.chart.client.attach_lpu;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/attach_lpu.html',
            scope: scope,
            size: 'lg'
        })
    };
    $scope.attach_lpu_edit = function () {
        open_attach_lpu_edit().result.then(function (result) {
            RisarApi.attach_lpu.save($scope.chart.client.id, result).then(function(result){
                $scope.chart.client.attach_lpu = result;
            });
        }, function(){
            reload_chart();
        });
    };

    reload_chart();
};
