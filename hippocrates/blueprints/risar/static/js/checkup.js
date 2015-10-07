
'use strict';

var CheckupCtrl = function ($scope, RisarApi, RefBookService, PrintingService, PrintingDialog, EMModalService,
                            EventMeasureService) {
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_talon = new PrintingService("risar");
    $scope.ps_talon.set_context("risar_talon");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.header.event.id
        }
    };

    $scope.ps_fi = new PrintingService("risar_inspection");
    $scope.ps_fi.set_context("risar_first_inspection");
    $scope.ps_si = new PrintingService("risar_inspection");
    $scope.ps_si.set_context("risar_second_inspection");
    $scope.ps_resolve_inspection = function () {
        return {
            event_id: $scope.header.event.id,
            action_id: $scope.checkup_id
        }
    };
    var params = aux.getQueryParams(window.location.search);
    var checkup_id = $scope.checkup_id = params.checkup_id;
    var event_id = $scope.event_id = params.event_id;

    var open_tab = function (tab_name){
        var prefix = "tab_";
        tab_name = tab_name.replace(/\//, '');
        $('.nav-pills a[href='+tab_name.replace(prefix,"")+']').tab('show');
    };
    var reload_checkup = function () {
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        if (!checkup_id) {
            RisarApi.checkup.create(event_id, $scope.getFlatCode()).
                then(function (checkup) {
                    $scope.checkup = checkup;
                });
        } else {
            RisarApi.checkup.get(checkup_id)
                .then(function (checkup) {
                    $scope.checkup = checkup;
                });
        }
    };

    $scope.generateMeasures = function () {
        RisarApi.measure.regenerate($scope.checkup.id).
            then(function (measures) {
                $scope.checkup.measures = measures;
            });
    };
    $scope.removeMeasures = function () {
        RisarApi.measure.remove($scope.checkup.id).
            then(function (measures) {
                $scope.checkup.measures = measures;
            });
    };
    $scope.viewEventMeasure = function (idx) {
        var em = $scope.checkup.measures[idx];
        EMModalService.openView(em);
    };
    $scope.cancelEm = function (idx) {
        var em = $scope.checkup.measures[idx];
        EventMeasureService.cancel(em)
            .then(function (upd_em) {
                $scope.checkup.measures.splice(idx, 1, upd_em);
            });
    };

    $scope.init = function () {
        var hash = document.location.hash;
        if (hash) {
            open_tab(hash);
        }
        reload_checkup();
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
};

var CheckupFirstEditCtrl = function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    var updateHW_Ratio = function (){
        $scope.checkup.hw_ratio = $scope.checkup.height ? Math.round(($scope.checkup.weight/$scope.checkup.height)*100) : NaN;
    };
    var updateBMI = function (){
        $scope.checkup.BMI = $scope.checkup.height ? ($scope.checkup.weight/Math.pow($scope.checkup.height/100,2)).toFixed(1) : NaN;
    };
    $scope.getFlatCode = function () {
        return 'risarFirstInspection';
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

    $scope.init();
};

var CheckupSecondEditCtrl = function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    $scope.getFlatCode = function () {
        return 'risarSecondInspection';
    };
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

    $scope.init();
};

WebMis20.controller('CheckupCtrl', ['$scope', 'RisarApi', 'RefBookService', 'PrintingService', 'PrintingDialog',
    'EMModalService', 'EventMeasureService', CheckupCtrl]);
WebMis20.controller('CheckupFirstEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi',
    'Config', CheckupFirstEditCtrl]);
WebMis20.controller('CheckupSecondEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi',
    'Config', CheckupSecondEditCtrl]);