/**
 * Created by mmalkov on 24.07.16.
 */
"use strict";
WebMis20

.controller('CheckupGynEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$filter', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, $filter, RisarApi, Config) {
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
    $scope.$watch('checkup.stomach', function (n, o) {
        if ( n!==o ) {
            
            var selectedCodes = _.map(n, function(obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ( $filter('intersects')(selectedCodes, ['painful', 'tense']) ) {
                $scope.isStomachAreaVisible = true;
            } else {
                $scope.checkup.stomach_area = null;
                $scope.isStomachAreaVisible = false;
            }
        }
    }, true);
    $scope.$watch('checkup.bimanual_body_of_womb_size', function (n, o) {
        if ( n!==o ) {
            var code = safe_traverse(n, ['code']);
            $scope.is_bimanual_body_of_womb_enlarged_Visible = code === 'enlarged' ? true : false;
            $scope.is_bimanual_body_of_womb_reduced_Visible = code === 'reduced' ? true : false;

            if (!$scope.is_bimanual_body_of_womb_enlarged_Visible) { $scope.checkup.bimanual_body_of_womb_enlarged=null; }
            if (!$scope.is_bimanual_body_of_womb_reduced_Visible) { $scope.checkup.bimanual_body_of_womb_reduced=null; }

        }
    }, true); 
    
    $scope.$watch('checkup.rectovaginal_body_of_womb_size', function (n, o) {
        if ( n!==o ) {
            var code = safe_traverse(n, ['code']);
            $scope.is_rectovaginal_body_of_womb_enlarged_Visible = code === 'enlarged' ? true : false;
            $scope.is_rectovaginal_body_of_womb_reduced_Visible = code === 'reduced' ? true : false;

            if (!$scope.is_rectovaginal_body_of_womb_enlarged_Visible) { $scope.checkup.rectovaginal_body_of_womb_enlarged=null; }
            if (!$scope.is_rectovaginal_body_of_womb_reduced_Visible) { $scope.checkup.rectovaginal_body_of_womb_reduced=null; }

        }
    }, true);
    
    $scope.$watch('checkup.rectal_body_of_womb_size', function (n, o) {
        if ( n!==o ) {
            var code = safe_traverse(n, ['code']);
            $scope.is_rectal_body_of_womb_enlarged_Visible = code === 'enlarged' ? true : false;
            $scope.is_rectal_body_of_womb_reduced_Visible = code === 'reduced' ? true : false;

            if (!$scope.is_rectal_body_of_womb_enlarged_Visible) { $scope.checkup.rectal_body_of_womb_enlarged=null; }
            if (!$scope.is_rectal_body_of_womb_reduced_Visible) { $scope.checkup.rectal_body_of_womb_reduced=null; }

        }
    }, true);
    $scope.parseTemperature = function (temperature) {
        temperature = parseFloat(temperature);
        if (!temperature) return null;
        return temperature % 1 === 0 ? temperature / 10 : temperature;
    };
    $scope.prepareCheckup = function() {
        $scope.checkup.diagnoses_changed = $scope.DiagForm.$dirty;
        $scope.checkup.temperature = $scope.parseTemperature($scope.checkup.temperature);
        $scope.checkup.temperature_rise = $scope.parseTemperature($scope.checkup.temperature_rise);
        return $scope.checkup;
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
    var fill_from_id = params.fill_from;

    var reload_checkup = function () {
        var checkup_promise;
        /* set header */
        RisarApi.gynecologic_chart.get_header(event_id)
            .then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
                $scope.clientBd = $scope.header.client.birth_date;
            });
        /* copy checkup */
        if (!checkup_id && fill_from_id !== undefined) {
            checkup_promise = RisarApi.checkup_gyn.get_copy(event_id, fill_from_id);
        /* create new checkup */
        } else if (!checkup_id) {
            checkup_promise = RisarApi.checkup_gyn.create(event_id, 'gynecological_visit_general_checkUp');
        /* get checkup */
        } else {
            checkup_promise = RisarApi.checkup_gyn.get(event_id, checkup_id);
        }
        checkup_promise.then(function (data) {
                $scope.setCheckupData(data);
                $scope.$broadcast('checkupLoaded');
            });
    };

    $scope.init();
    reload_checkup();
}])
;