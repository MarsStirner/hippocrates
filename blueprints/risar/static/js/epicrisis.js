
'use strict';
var EpicrisisCtrl = function ($timeout, $scope, RefBookService, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.rbRisarPregnancy_Final = RefBookService.get('rbRisarPregnancy_Final');

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

    var init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash.match('child') ? open_tab('#sixth') : open_tab(hash);
        }
        reload_epicrisis();
    };
    init();

};