/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('CheckupFirstEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$filter', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, $filter, RisarApi, Config) {
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
                        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id, '_self');
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

   $scope.$watch('checkup.stomach', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['jivotnaprajennyj', 'jivotboleznennyi'])) {
                $scope.isStomachAreaVisible = true;
            } else {
                $scope.checkup.stomach_area = null;
                $scope.isStomachAreaVisible = false;
            }
        }
    }, true);
    
    $scope.$watch('checkup.complaints', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['other'])) {
                $scope.isComplaintsFreeInputVisible = true;
            } else {
                $scope.checkup.complaints_free_input = null;
                $scope.isComplaintsFreeInputVisible = false;
            }
        }
    }, true);
    
    $scope.$watch('checkup.cervix', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['other'])) {
                $scope.isCervixFreeInputVisible = true;
            } else {
                $scope.checkup.cervix_free_input = null;
                $scope.isCervixFreeInputVisible = false;
            }
        }
    }, true);
    
    $scope.$watch('checkup.cervical_canal', function (n, o) {
        if (n !== o) {
            var code = n ? safe_traverse(n, ['code']) : undefined;
            if (code === 'other') {
                $scope.isCervicalCanalFreeInputVisible = true;
            } else {
                $scope.checkup.cervical_canal_free_input = null;
                $scope.isCervicalCanalFreeInputVisible = false;
            }
        }
    }, true);

    $scope.$watch('checkup.body_of_womb', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['enlarged'])) {
                $scope.isBodyOfWombAdditionalVisible = true;
            } else {
                $scope.checkup.body_of_womb_additional = null;
                $scope.isBodyOfWombAdditionalVisible = false;
            }
        }
    }, true);
    
     $scope.$watch('checkup.appendages', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['uveliceny'])) {
                $scope.isAppendasIncreasedVisible = true;
            } else {
                $scope.checkup.appendages_increased = null;
                $scope.isAppendasIncreasedVisible = false;
            }
        }
    }, true);
    
    $scope.$watch('checkup.appendages_right', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['uveliceny'])) {
                $scope.isAppendasRightIncreasedVisible = true;
            } else {
                $scope.checkup.appendages_right_increased = null;
                $scope.isAppendasRightIncreasedVisible = false;
            }
        }
    }, true);

    $scope.init();
    reload_checkup();
}])
;