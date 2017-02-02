/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('CheckupSecondEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$filter', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, $filter, RisarApi, Config) {
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
    
    $scope.$watch('checkup.stomach', function (n, o) {
        if (n !== o) {
            var selectedCodes = _.map(n, function (obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ($filter('intersects')(selectedCodes, ['other', 'jivotboleznennyi'])) {
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

    $scope.init();
    reload_checkup();
}])
;