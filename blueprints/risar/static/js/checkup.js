
'use strict';
var CheckupCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id
    var event_id = $scope.event_id = params.event_id;
    var create_new_checkup = function (){
        $scope.checkup = {height: NaN,
                          weight: NaN}
    }
    var reload_checkup = function () {
        RisarApi.chart.get(event_id)
        .then(function (data) {
            $scope.chart = data.event;
            $scope.client_id = data.event.client.id;
            $scope.checkup = data.event.checkups.filter(function(elem){return elem.id == checkup_id})[0]
            if (!$scope.checkup) create_new_checkup();
        })
    };

    reload_checkup();
}

var CheckupFirstEditCtrl = function ($scope, $window, $document, RisarApi, Config) {
    var updateHW_Ratio = function (){
        $scope.checkup.hw_ratio = $scope.checkup.height ? Math.round(($scope.checkup.weight/$scope.checkup.height)*100) : NaN;
    }
    var updateBMI = function (){
        $scope.checkup.BMI = $scope.checkup.height ? ($scope.checkup.weight/Math.pow($scope.checkup.height/100,2)).toFixed(1) : NaN;
    }
    $scope.$watch('checkup.height', function() {
        if ($scope.checkup.height && (!isNaN($scope.checkup.weight))){
        updateHW_Ratio();
        updateBMI();
        }

    });
    $scope.$watch('checkup.weight', function() {
        if (!isNaN($scope.checkup.weight)){
            updateHW_Ratio();
            updateBMI();
        }
    });
    $scope.save = function () {
        var form = $scope.CheckupFirstEditForm;
        if (form.$invalid) {
            var formelm = $('#CheckupFirstEditForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        if($scope.checkup){
            $scope.checkup.flat_code = 'risarFirstInspection';
        } else {
            $scope.checkup = {flat_code: 'risarFirstInspection'};
        }
        var model = $scope.checkup;
        RisarApi.checkup.save($scope.event_id, model)
        .then(function (data) {
            if($scope.checkup.id){
                $scope.checkup = data;
            } else {
                $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id + '&checkup_id=' + data.id, '_self');
            }

        })
    }
};

var CheckupSecondEditCtrl = function ($scope, $window, $document, RisarApi, Config) {

    $scope.save = function () {
        if($scope.checkup){
            $scope.checkup.flat_code = 'risarSecondInspection';
        } else {
            $scope.checkup = {flat_code: 'risarSecondInspection'};
        }
        var model = $scope.checkup;
        RisarApi.checkup.save($scope.event_id, model)
        .then(function (data) {
            if($scope.checkup.id){
                $scope.checkup = data;
            } else {
                $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.chart.id + '&checkup_id=' + data.id, '_self');
            }

        })
    }
};

WebMis20.controller('CheckupCtrl', ['$scope', 'RisarApi', CheckupCtrl]);
WebMis20.controller('CheckupFirstEditCtrl', ['$scope', '$window', '$document', 'RisarApi', 'Config', CheckupFirstEditCtrl]);