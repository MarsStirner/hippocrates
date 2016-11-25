
'use strict';

WebMis20.controller('CheckupPuerperaEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config', 
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});
    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        return $scope.checkup
    };
    $scope.save = function (form_controller) {
        if (form_controller.$invalid) {
            return false;
        }
        return RisarApi.checkup_puerpera.save($scope.event_id, $scope.prepareCheckup())
            .then(function (data) {
                if($scope.checkup.id){
                    $scope.checkup = data;
                } else {
                    $window.open(Config.url.inspection_puerpera_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.id, '_self');
                }
            });
    };
    $scope.save_forward = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            RisarApi.checkup_puerpera.save($scope.event_id, $scope.prepareCheckup())
                .then(function (data) {
                    if($scope.checkup.id){
                        $scope.checkup = data;
                        $scope.rc.sampleWizard.forward();
                        $location.url($scope.rc.sampleWizard.currentStep.attributes.id);
                    } else {
                        $scope.rc.sampleWizard.forward();
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.inspection_puerpera_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.id+'#/'+tab_name, '_self');
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
                $scope.minDate = $scope.header.event.set_date;
            });
        if (!checkup_id) {
            RisarApi.checkup_puerpera.create(event_id, 'risarPuerperaCheckUp').
            then(function (checkup) {
                $scope.checkup = checkup;
                $scope.$broadcast('checkupLoaded');
            });
        } else {
            RisarApi.checkup_puerpera.get(checkup_id)
                .then(function (checkup) {
                    $scope.checkup = checkup;
                    $scope.$broadcast('checkupLoaded');
                });
        }
    };

    $scope.init();
    reload_checkup();
}])
;
