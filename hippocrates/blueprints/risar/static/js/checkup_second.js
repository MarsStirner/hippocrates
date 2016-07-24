/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('CheckupSecondEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            return RisarApi.checkup.save($scope.event_id, $scope.checkup)
                .then(function (data) {
                    if ($scope.checkup.id){
                        $scope.checkup = data;
                    } else {
                        $window.open(Config.url.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.id, '_self');
                    }
                });
        }
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
            RisarApi.checkup.create(event_id, 'risarSecondInspection').
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