/**
 * Created by mmalkov on 24.07.16.
 */
"use strict";
WebMis20

.controller('CheckupGynEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    var update_auto = function () {
        if (!$scope.checkup) return;
        try {
            if (! $scope.checkup.height || ! $scope.checkup.weight || $scope.checkup.height < 10 || $scope.checkup.weight < 10) {
                //noinspection ExceptionCaughtLocallyJS
                throw NaN;
            }
            $scope.checkup.mrk = Math.round(100 * $scope.checkup.weight / $scope.checkup.height);
            $scope.checkup.imt = ($scope.checkup.weight / Math.pow($scope.checkup.height/100, 2) ).toFixed(1);
        } catch (e) {
            $scope.checkup.mrk = NaN;
            $scope.checkup.imt = NaN;
        }
    };

    $scope.$watch('checkup.height', update_auto);
    $scope.$watch('checkup.weight', update_auto);

    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        return $scope.checkup
    };
    $scope.save = function (form_controller){
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            return RisarApi.checkup_gyn.save($scope.event_id,  $scope.prepareCheckup())
                .then(function (data) {
                    if ($scope.checkup.id){
                        $scope.setCheckupData(data);
                    } else {
                        $window.open(Config.url.gyn.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id, '_self');
                    }
                });
        }
    };
    $scope.save_forward = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid){
            RisarApi.checkup_gyn.save($scope.event_id,  $scope.prepareCheckup())
                .then(function (data) {
                    if($scope.checkup.id){
                        $scope.setCheckupData(data);
                        $scope.rc.sampleWizard.forward();
                        $location.url($scope.rc.sampleWizard.currentStep.attributes.id);
                    } else {
                        $scope.rc.sampleWizard.forward();
                        var tab_name = $scope.rc.sampleWizard.currentStep.attributes.id;
                        $window.open(Config.url.gyn.inpection_edit_html + '?event_id=' + $scope.header.event.id + '&checkup_id=' + data.checkup.id+'#/'+tab_name, '_self');
                    }
                });
        }
    };
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;

    var reload_checkup = function () {
        RisarApi.gynecologic_chart.get_header(event_id)
            .then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
                $scope.clientBd = $scope.header.client.birth_date;
            });
        if (!checkup_id) {
            return RisarApi.checkup_gyn.create(event_id, 'gynecological_visit_general_checkUp')
                .then(function (data) {
                    $scope.setCheckupData(data);
                    $scope.$broadcast('checkupLoaded');
                    return data;
                });
        } else {
            return RisarApi.checkup_gyn.get(event_id, checkup_id)
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