/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('CheckupFirstEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    var updateHW_Ratio = function (){
        $scope.checkup.hw_ratio = $scope.checkup.height ? Math.round(($scope.checkup.weight/$scope.checkup.height)*100) : NaN;
    };
    var updateBMI = function (){
        $scope.checkup.BMI = $scope.checkup.height ? ($scope.checkup.weight/Math.pow($scope.checkup.height/100,2)).toFixed(1) : NaN;
    };
    $scope.$watch('checkup.height', function() {
        if ($scope.checkup && $scope.checkup.height && (!isNaN($scope.checkup.weight))) {
            updateHW_Ratio();
            updateBMI();
        }
    });
    $scope.$watch('checkup.weight', function() {
        if ($scope.checkup && !isNaN($scope.checkup.weight)) {
            updateHW_Ratio();
            updateBMI();
        }
    });
    $scope.save = function (form_controller) {
        if (form_controller.$invalid) {
            //var formelm = $('#CheckupFirstEditForm').find('.ng-invalid:not(ng-form):first');
            //$document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        return RisarApi.checkup.save($scope.event_id, $scope.checkup)
            .then(function (data) {
                if($scope.checkup.id){
                    $scope.checkup = data;
                } else {
                    $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.id, '_self');
                }
            });
    };
    $scope.save_forward = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            RisarApi.checkup.save($scope.event_id, $scope.checkup)
                .then(function (data) {
                    if($scope.checkup.id){
                        $scope.checkup = data;
                        $scope.rc.sampleWizard.forward();
                        $location.url($scope.rc.sampleWizard.currentStep.attributes.id);
                    } else {
                        $scope.rc.sampleWizard.forward();
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.id+'#/'+tab_name, '_self');
                    }
                });
        }
    };
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;

    var reload_checkup = function () {
        RisarApi.chart.get_header(event_id).
        then(function (data) {
            $scope.header = data.header;
        });
        if (!checkup_id) {
            RisarApi.checkup.create(event_id, 'risarFirstInspection').
            then(function (checkup) {
                $scope.checkup = checkup;
                if(!$scope.checkup.fetuses.length) {
                    $scope.add_child();
                }
            });
        } else {
            RisarApi.checkup.get(checkup_id)
                .then(function (checkup) {
                    $scope.checkup = checkup;
                    if(!$scope.checkup.fetuses.length) {
                        $scope.add_child();
                    }
                });
        }
    };

    $scope.init();
    reload_checkup();
}])
;