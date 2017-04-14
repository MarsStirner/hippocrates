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
    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        return $scope.checkup
    };

    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid) {
            return RisarApi.checkup.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if ($scope.checkup.id) {
                        $scope.setCheckupData(data);
                    } else {
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id + '#/'+tab_name, '_self');
                    }
                });
        }
    };
    $scope.save_forward = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            RisarApi.checkup.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if($scope.checkup.id){
                        $scope.setCheckupData(data);
                        $scope.rc.sampleWizard.forward();
                        $location.url($scope.rc.sampleWizard.currentStep.attributes.id);
                    } else {
                        $scope.rc.sampleWizard.forward();
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id+'#/'+tab_name, '_self');
                    }
                });
        }
    };
    $scope.calcFetusFisherKtgInfo = function (fetus_data) {
        RisarApi.fetus.calc_fisher_ktg(fetus_data)
            .then(function (result) {
                fetus_data.fisher_ktg_points = result.points;
                fetus_data.fisher_ktg_rate = result.fisher_ktg_rate;
                if (result.points === 0) {
                    fetus_data.fisher_ktg_points = null;
                    fetus_data.fisher_ktg_rate = null;
                }
            });
    };
    $scope.$on('mayBeUziSrokChanged', function() {
        RisarApi.checkup.get($scope.checkup_id)
            .then(function (data) {
                $scope.checkup.calculated_pregnancy_week_by_ultrason = data.checkup.calculated_pregnancy_week_by_ultrason;
            });
    });

    var reload_checkup = function () {
        $scope.getHeader();
        $scope.getCheckup('risarFirstInspection');
    };

    $controller('BasePregCheckupWatchesCtrl', {$scope: $scope});

    $scope.init();
    reload_checkup();
}]);