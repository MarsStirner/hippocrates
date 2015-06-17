
'use strict';
var EpicrisisCtrl = function ($timeout, $scope, RefBookService, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.rbRisarPregnancy_Final = RefBookService.get('rbRisarPregnancy_Final');
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.is_empty = function (obj) {
        return angular.equals({}, obj);
    };

    var open_tab = function (tab_name){
        var prefix = "tab_";
        tab_name = tab_name.replace(/\//, '');
        $('.nav-pills a[href='+tab_name.replace(prefix,"")+']').tab('show');

        // Change hash for page-reload
        $('.nav-pills a').on('shown.bs.tab', function (e) {
            window.location.hash = e.target.hash.replace("#", "#" + prefix);
        })
    };

    var reload_epicrisis = function () {
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;

            if($scope.chart.checkups.length){
                var first_checkup = $scope.chart.checkups[0];
                $scope.weight_gain = $scope.chart.checkups[$scope.chart.checkups.length-1].weight - first_checkup.weight; //прибавка массы за всю беременность
            }

            if (!$scope.chart.epicrisis) {
                $scope.chart.epicrisis = {
                    pregnancy_final: $scope.rbRisarPregnancy_Final.get_by_code('rodami'),
                    newborn_inspections : [{}],
                    attend_diagnosis: [],
                    complicating_diagnosis: [],
                    operation_complication:[]};
            }
            $timeout(function(){
                var hash = document.location.hash;
                if (hash.match('child')){
                    open_tab(hash);
                }
            }, 0);
        })
    };

    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            var model = $scope.chart.epicrisis;
            RisarApi.epicrisis.save($scope.chart.id, model)
            .then(function (data) {
                $scope.chart.epicrisis = data;
            })
        }

    };

    $scope.close_event = function () {
        RisarApi.chart.close_event($scope.chart.id, $scope.chart)
        .then(function (data) {
            $scope.chart = data;
        })
    };

    $scope.add_child = function (){
        $scope.chart.epicrisis.newborn_inspections.push({});
        $timeout(function(){
            $('#childrenTabs a:last').tab('show');
        }, 0);

    };

    $scope.newborn_inspection_delete = function(inspection){
        if(inspection.id){
            RisarApi.epicrisis.newborn_inspections.delete(inspection.id)
            .then(function () {
                inspection.deleted = 1;
            })
        }
    };

    $scope.newborn_inspection_restore = function(inspection){
        if(inspection.id){
            RisarApi.epicrisis.newborn_inspections.undelete(inspection.id)
            .then(function () {
                inspection.deleted = 0;
            })
        }
    };

    $scope.alive_changed = function(child_info){
        if (child_info.alive){
            child_info.date = null;
            child_info.time = null;
            child_info.death_reason = null;
        } else {
            child_info.date = null;
            child_info.time = null;
            child_info.maturity_rate = null;
            child_info.apgar_score_1 = null;
            child_info.apgar_score_5 = null;
            child_info.apgar_score_10 = null;
        }
    }

    $scope.$watch('chart.epicrisis.delivery_date', function() {
        if($scope.chart && !$scope.chart.epicrisis.pregnancy_duration && $scope.chart.epicrisis.delivery_date &&
            $scope.chart.card_attributes.pregnancy_start_date){
            var delivery_date = moment($scope.chart.epicrisis.delivery_date);
            var pregnancy_start_date = moment($scope.chart.card_attributes.pregnancy_start_date)
            $scope.chart.epicrisis.pregnancy_duration = Math.floor(delivery_date.diff(pregnancy_start_date, 'days')/7) + 1;
        }
    });

    var init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash.match('child') ? open_tab('#sixth') : open_tab(hash);
        }
        reload_epicrisis();
    };
    init();

};