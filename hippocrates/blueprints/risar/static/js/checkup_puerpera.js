
'use strict';

WebMis20.controller('CheckupPuerperaEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config', 
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});
    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        return $scope.checkup
    };
    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid) {
            return RisarApi.checkup_puerpera.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if ($scope.checkup.id) {
                        $scope.setCheckupData(data);
                    } else {
                        $window.open(Config.url.inspection_puerpera_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id, '_self');
                    }
                });
        }
    };
    $scope.save_forward = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            RisarApi.checkup_puerpera.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if($scope.checkup.id){
                        $scope.setCheckupData(data);
                        $scope.rc.sampleWizard.forward();
                        $location.url($scope.rc.sampleWizard.currentStep.attributes.id);
                    } else {
                        $scope.rc.sampleWizard.forward();
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.inspection_puerpera_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id+'#/'+tab_name, '_self');
                    }
                });
        }
    };

    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;

    var reload_checkup = function () {
        $scope.getHeader();

        if (!checkup_id) {
            return RisarApi.checkup_puerpera.create(event_id, 'risarPuerperaCheckUp')
                .then(function (data) {
                    $scope.setCheckupData(data);
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        } else {
            return RisarApi.checkup_puerpera.get(checkup_id)
                .then(function (data) {
                    $scope.setCheckupData(data);
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        }
    };

    $scope.init();
    reload_checkup();
}])
;
