'use strict';
var EpicrisisCtrl = function ($timeout, $scope, $q, RefBookService, RisarApi, PrintingService, PrintingDialog, PropsDescriptor, epicrisis_descriptor) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.rbRisarPregnancy_Final = RefBookService.get('rbRisarPregnancy_Final');
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_epicrisis = new PrintingService("risar");
    $scope.ps_epicrisis.set_context("risar_epicrisis");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };
    $scope.is_empty = function (obj) {
        return angular.equals({}, obj);
    };
    $scope.currentDate = new Date();
    $scope.minDate = new Date();
    $scope.epicrisisDescriptor = new PropsDescriptor(epicrisis_descriptor);

    var open_tab = function (tab_name) {
        var prefix = "tab_";
        tab_name = tab_name.replace(/\//, '');
        $('.nav-pills a[href=' + tab_name.replace(prefix, "") + ']').tab('show');

        // Change hash for page-reload
        $('.nav-pills a').on('shown.bs.tab', function (e) {
            window.location.hash = e.target.hash.replace("#", "#" + prefix);
        })
    };

    var reload_epicrisis = function () {
        RisarApi.chart.get_header(event_id).then(function (data) {
            $scope.header = data.header;
            $scope.minDate = $scope.header.event.set_date;
        });
        RisarApi.epicrisis.get(event_id)
            .then(function (result) {
                $scope.epicrisis = result.epicrisis;
                $scope.chart = result.chart;
                $scope.mother_death = $scope.epicrisis ? Boolean($scope.epicrisis.death_date) : false;
                if (!$scope.epicrisis) {
                    $scope.epicrisis = {
                        pregnancy_final: $scope.rbRisarPregnancy_Final.get_by_code('rodami'),
                        newborn_inspections: [{}],
                        diagnoses: []
                    };
                }
                $scope.epicrisis.diagnosis_pathanatomical = $scope.filterRb($scope.epicrisis.diagnosis_types, 'pathanatomical');
                $scope.epicrisis.diagnosis_final = $scope.filterRb($scope.epicrisis.diagnosis_types, 'final');
                $timeout(function () {
                    var hash = document.location.hash;
                    if (hash.match('child')) {
                        open_tab(hash);
                    }
                }, 0);
            })
    };

    $scope.save = function (form_controller) {
        form_controller.submit_attempt = true;
        if (form_controller.$valid) {
            var model = $scope.epicrisis;
            return RisarApi.epicrisis.save($scope.event_id, model)
                .then(function (data) {
                    $scope.epicrisis = data.epicrisis;
                    $scope.epicrisis.diagnosis_pathanatomical = $scope.filterRb($scope.epicrisis.diagnosis_types, 'pathanatomical');
                    $scope.epicrisis.diagnosis_final = $scope.filterRb($scope.epicrisis.diagnosis_types, 'final');
                    $scope.chart = data.chart;
                })
        }

    };
    $scope.is_save_disabled = function (wizard) {
        return !!(wizard.currentIndex == 1 && $scope.mother_death && wizard.currentStep.formController.$invalid);
    };

    $scope.add_child = function () {
        $scope.epicrisis.newborn_inspections.push({
            id: null,
            deleted: 0
        });
        $timeout(function () {
            $('#childrenTabs').find('a:last').tab('show');
        }, 0);

    };

    $scope.delete_child = function(child){
        child.deleted = 1;
        $timeout(function(){
            $('#childrenTabs li.active').removeClass('active');
            $('#childrenTabs').find('a:first').tab('show');
        }, 0);
    };

    $scope.filterRb = function (list, code) {
        var res = [];
        if(list) {
            list.forEach(function(el) {
                if(el.code == code) {
                    res.push(el);
                    return res;
                }
            });
        }
        return res;
    };

    $scope.hospMedicoFilter = function () {
        return {
            org_id: safe_traverse($scope.epicrisis, ['LPU', 'id'], undefined)
        }
    };

    $scope.newborn_inspection_delete = function (inspection) {
        if (inspection.id) {
            RisarApi.epicrisis.newborn_inspections.delete(inspection.id)
                .then(function () {
                    inspection.deleted = 1;
                })
        }
    };

    $scope.newborn_inspection_restore = function (inspection) {
        if (inspection.id) {
            RisarApi.epicrisis.newborn_inspections.undelete(inspection.id)
                .then(function () {
                    inspection.deleted = 0;
                })
        }
    };

    $scope.alive_changed = function (child_info) {
        if (child_info.alive) {
            child_info.date = null;
            child_info.time = null;
            child_info.death_reasons = null;
        } else {
            child_info.date = null;
            child_info.time = null;
            child_info.maturity_rate = null;
            child_info.apgar_score_1 = null;
            child_info.apgar_score_5 = null;
            child_info.apgar_score_10 = null;
        }
    };

    $scope.$watch('chart.epicrisis.delivery_date', function () {
        if ($scope.chart && !$scope.epicrisis.pregnancy_duration && $scope.epicrisis.delivery_date &&
            $scope.chart.pregnancy_start_date) {
            var delivery_date = moment($scope.epicrisis.delivery_date);
            var pregnancy_start_date = moment($scope.chart.pregnancy_start_date);
            $scope.epicrisis.pregnancy_duration = Math.floor(delivery_date.diff(pregnancy_start_date, 'days') / 7) + 1;
        }
    });
    $scope.$watch('mother_death', function (n) {
        if ($scope.epicrisis && !n) {
            $scope.epicrisis.reason_of_death = null;
            $scope.epicrisis.death_date = null;
            $scope.epicrisis.death_time = null;
            $scope.epicrisis.pat_diagnosis = null;
            $scope.epicrisis.control_expert_conclusion = '';
        }
    });
    $scope.$watch('epicrisis.pregnancy_final', function (n, o) {
        if (n) {
            $scope.min_pregnancy_duration = n.code == 'abortom' ? 0 : 22;
            $scope.max_pregnancy_duration = n.code == 'abortom' ? 21 : 45;
            if (o && n.code !== o.code){
                $scope.epicrisis.pregnancy_duration = undefined;
            }
        }
    });
    $scope.$watch('epicrisis.LPU', function (n, o) {
        if (o !== undefined && !angular.equals(n, o)) {
            $scope.epicrisis.maternity_hosp_medico = null;
        }
    });

    var init = function () {
        var hash = document.location.hash;
        if (hash) {
            hash.match('child') ? open_tab('#sixth') : open_tab(hash);
        }
        reload_epicrisis();
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
    $scope.print_self = function () {
        RisarApi.print_jsp_epicrisis({action_id: $scope.epicrisis.printing_action_id, extension: 'html'});
    };
    init();

};