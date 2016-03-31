
'use strict';

var CheckupCtrl = function ($scope, $timeout, RisarApi, RefBookService, PrintingService, PrintingDialog) {
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
            RisarApi.checkup_puerpera.create(event_id, $scope.getFlatCode()).
                then(function (checkup) {
                    $scope.checkup = checkup;
                });
        } else {
            RisarApi.checkup_puerpera.get(checkup_id)
                .then(function (checkup) {
                    $scope.checkup = checkup;
                });
        }
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
    $scope.$watch('checkup.pregnancy_continuation', function (newVal) {
        if (newVal) {  // если "Да", то очистить
            $scope.checkup.pregnancy_continuation_refusal = null;
        }
    });
    $scope.pregContRefusalDisabled = function () {
        if (!$scope.checkup) return true;
        return Boolean($scope.checkup.pregnancy_continuation === null || $scope.checkup.pregnancy_continuation);  // задизейблено при "Да"
    };
    $scope.pregContRefusalRequired = function () {
        if (!$scope.checkup) return false;
        return !Boolean($scope.checkup.pregnancy_continuation);  // требуется при "Нет"
    };
};

var CheckupPuerperaEditCtrl = function ($scope, $controller, $window, $location, $document, RisarApi, Config) {
    $controller('CheckupCtrl', {$scope: $scope});

    $scope.getFlatCode = function () {
        return 'risarPuerperaCheckUp';
    };
    $scope.save = function (form_controller) {
        if (form_controller.$invalid) {
            return false;
        }
        return RisarApi.checkup_puerpera.save($scope.event_id, $scope.checkup)
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
            RisarApi.checkup_puerpera.save($scope.event_id, $scope.checkup)
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

    $scope.init();
};

WebMis20.controller('CheckupCtrl', ['$scope', '$timeout', 'RisarApi', 'RefBookService', 'PrintingService', 'PrintingDialog',
    CheckupCtrl]);
WebMis20.controller('CheckupPuerperaEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', 'RisarApi',
    'Config', CheckupPuerperaEditCtrl]);