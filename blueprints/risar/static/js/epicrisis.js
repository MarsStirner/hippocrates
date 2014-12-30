
'use strict';
var EpicrisisCtrl = function ($timeout, $scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;

    var open_tab = function (tab_name){
        var prefix = "tab_";
        tab_name = tab_name.replace(/\//, '');
        $('.nav-pills a[href='+tab_name.replace(prefix,"")+']').tab('show');

        // Change hash for page-reload
        $('.nav-pills a').on('shown.bs.tab', function (e) {
            window.location.hash = e.target.hash.replace("#", "#" + prefix);
        })
    }

    var reload_epicrisis = function () {
        RisarApi.chart.get(event_id)
        .then(function (data) {
            $scope.chart = data.event;
            if (!$scope.chart.epicrisis){
                $scope.chart.epicrisis = {'newborn_inspections' : [{}]};
            }
            $timeout(function(){
                var hash = document.location.hash;
                if (hash.match('child')){
                    open_tab(hash);
                }
            }, 0);
        })
    };

    $scope.save = function () {
        var model = $scope.chart.epicrisis;
        RisarApi.epicrisis.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.epicrisis = data;
        })
    }
    $scope.add_child = function (){
        $scope.chart.epicrisis.newborn_inspections.push({});
        $timeout(function(){
            $('#childrenTab a:last').tab('show');
        }, 0);

    }
    var init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash.match('child') ? open_tab('#last') : open_tab(hash);
        }
        reload_epicrisis();
    };
    init();

}