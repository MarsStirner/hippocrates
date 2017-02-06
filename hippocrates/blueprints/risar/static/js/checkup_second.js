/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('CheckupSecondEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        return $scope.checkup
    };
    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            return RisarApi.checkup.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if ($scope.checkup.id){
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

    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var fill_from_id = params.fill_from;
    var event_id = $scope.event_id = params.event_id;

    $scope._getCheckup = function (flat_code) {
        if (!checkup_id && fill_from_id !== undefined) {
            return RisarApi.checkup.get_copy(event_id, fill_from_id)
                .then(function (data) {
                    $scope.setCheckupData(data);
                    if(!$scope.checkup.fetuses.length) {
                        $scope.add_child();
                    }
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        } else {
            return $scope.getCheckup(flat_code);
        }
    };
    var reload_checkup = function () {
        $scope.getHeader();
        $scope._getCheckup('risarSecondInspection');
    };
    $controller('BasePregCheckupWatchesCtrl', {$scope: $scope});
    $scope.init();
    reload_checkup();
}])
.controller('CheckupSecondChildCtrl', ['$scope', function ($scope) {
    function cleanPhisher() {
        $scope.child.state.basal = null;
        $scope.child.state.variability_range = null;
        $scope.child.state.frequency_per_minute = null;
        $scope.child.state.acceleration = null;
        $scope.child.state.deceleration = null;
        $scope.child.state.fisher_ktg_rate = null;
    }
    function cleanStv() {
        $scope.child.state.stv_evaluation = null;
    }
    $scope.$watch('child.state.ktg_input', function (n, o) {
        if (n === 'fisher') {
            $scope.isPhisher = true;
            $scope.isStv = false;
            cleanStv();
        } else if (n === 'stv') {
            $scope.isStv = true;
            $scope.isPhisher = false;
            cleanPhisher();
        } else {
          $scope.isPhisher = false;
          $scope.isStv = false;
        }
    }, true);
    $scope.$watch('child.state.stv_evaluation', function (n, o) {
        if (n !== undefined) {
            $scope.stvDescription = n < 4 ? 'патология' : 'норма';
        }
    }, true);
    
}]);
;