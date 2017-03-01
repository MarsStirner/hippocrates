/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var AnamnesisBaseCtrl = function ($scope, RisarApi, RefBookService, PrintingService, PrintingDialog) {
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };

    var params = aux.getQueryParams(window.location.search);
    $scope.event_id = params.event_id;
    $scope.reload_header = function () {
        return RisarApi.chart.get_header($scope.event_id).
            then(function (data) {
                $scope.header = data.header;
            });
    };
    $scope.open_print_window = function () {
        if ($scope.ps.is_available()) {
            PrintingDialog.open($scope.ps, $scope.$parent.$eval($scope.ps_resolve));
        }
    };
};

var BaseAnamnesisCtrl = function ($scope, $controller, RisarApi) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});

    var tabs = $scope.tabs = {
        motherfather: true,
        pregnancies: false,
        transfusions: false,
        intolerances: false
    };
    var hash = window.location.hash;
    if (hash.length > 1) {
        hash = hash.substr(1);
        if (_(tabs).keys().has(hash)) {
            tabs[hash] = true
        }
    }
    $scope.format_multiple = function (obj, attr) {
        if (!obj) { return '' }
        return _.map(obj, function (o) { return o[attr]; }).join(', ');
    };
};

var PregnancyAnamnesisCtrl = function ($scope, $controller, RisarApi, PropsDescriptor, mother_anamnesis_descriptor, prev_preg_descriptor) {
    $controller('BaseAnamnesisCtrl', {$scope: $scope});

    $scope.motherAnamnesisDescriptor = new PropsDescriptor(mother_anamnesis_descriptor);
    $scope.prevPregDescriptor = new PropsDescriptor(prev_preg_descriptor);
    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.anamnesis.get($scope.event_id)
            .then(function (data) {
                $scope.client_id = data.client_id;
                $scope.anamnesis = data.anamnesis;
            })
    };
    reload_anamnesis();
    $scope.print_anam = function (event_id) {
        RisarApi.print_jsp_anamnesis({event_id: event_id, extension: 'html'});
    };
};

var GynecologicalAnamnesisCtrl = function ($scope, $controller, $location, $timeout, RisarApi, PropsDescriptor, gyn_anamnesis_descriptor, prev_preg_descriptor) {
    $controller('BaseAnamnesisCtrl', {$scope: $scope});
    $scope.gynAnamnesisDescriptor = new PropsDescriptor(gyn_anamnesis_descriptor);
    $scope.prevPregDescriptor = new PropsDescriptor(prev_preg_descriptor);
    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.gynecological_anamnesis.get($scope.event_id)
            .then(function (data) {
                $scope.client_id = data.client_id;
                $scope.anamnesis = data;
            });

    };
    $scope.init = function () {
        var hash = $location.url().replace('/', '');
        if (hash === "pregnancies" ){
            $timeout(function(){
               $("li[active='tabs.pregnancies'] a").click();
            }, 0);
        }
        reload_anamnesis();

    };
    $scope.init();
    $scope.print_gyn_anam = function (event_id) {
        RisarApi.print_jsp_gyn_anamnesis({event_id: event_id, extension: 'html'});
    };
};

var MotherFatherCtrl = function ($scope) {
    $scope.warnings = {
        blood_type: 'Несовместимый резус-фактор',
        risk_group_07: 'Внимание! Возможно развитие групповой несовместимости'
    };
};
var PregnanciesCtrl = function ($scope, $modal, $timeout, RefBookService, RisarApi) {
    var miscarriage_codes = ['therapeutic_abortion_before_12', 'therapeutic_abortion', 'misbirth_before_11', 'misbirth_before_12-21', 'unknown_miscarriage'];
    $scope.rbGender = RefBookService.get('Gender');
    $scope.add = function () {
        var model = {
            newborn_inspections: []
        };
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            result.newborn_inspections = result.newborn_inspections.filter(function(inspection){
                return !inspection.deleted || inspection.id
            });
            RisarApi.anamnesis.pregnancies.save($scope.event_id, result).then(function (result) {
                $scope.anamnesis.pregnancies.push(result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        })
    };
    $scope.edit = function (p) {
        var model = angular.extend({}, p);
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            result.newborn_inspections = result.newborn_inspections.filter(function(inspection){
                return !inspection.deleted || inspection.id
            });
            RisarApi.anamnesis.pregnancies.save($scope.event_id, result).then(function (result) {
                angular.extend(p, result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        });
    };

    $scope.remove = function (p) {
        if (p.id) {
            RisarApi.anamnesis.pregnancies.delete($scope.event_id, p.id).then(function () {
                p.deleted = 1;
            });
        } else {
            p.deleted = 1;
        }
    };
    $scope.restore = function (p) {
        if (p.id) {
            RisarApi.anamnesis.pregnancies.undelete($scope.event_id, p.id).then(function () {
                p.deleted = 0;
            });
        } else {
            p.deleted = 0;
        }
    };
    $scope.format_newborn_inspection = function (child) {
        if (!child) { return '' }
        var result = [];
        result.push((child.alive)?('живой'):('мёртвый'));
        if (child.sex){
            result.push('пол: {0}'.formatNonEmpty(child.sex.name));
        }
        result.push('масса: {0}'.formatNonEmpty(child.weight));
        if(child.abnormal_development){
            result.push('аномалии развития');
        }
        if(child.neurological_disorders){
            result.push('неврологические нарушения');
        }
        if (!child.alive && child.died_at) {
            result.push(child.died_at.name);
        }
        if (!child.alive && child.death_reason) {
            result.push('причина смерти: ' + child.death_reason);
        }
        return result.join(', ');
    };
    $scope.format_characteristics = function (p) {
        if (!p) { return '' }
        var result = [];
        if (p.note) {
            result.push(p.note)
        }
        if (p.maternity_aid && p.maternity_aid.length > 0) {
            result.push('Пособия, операции: ' + _.map(p.maternity_aid, function (ma) { return ma.name; }).join(', '));
        }
        var operation_testimonials = safe_traverse(p, ['operation_testimonials', 'name']);
        if (p.operation_testimonials) {
                result.push('Показания к операции: ' + operation_testimonials);
        }
        if (p.pregnancy_pathology && p.pregnancy_pathology.length) {
            result.push('Патологии беременности: ' + _.map(p.pregnancy_pathology, function (pat) {
                return pat.name;
            }).join(', '))
        }
        if (p.delivery_pathology && p.delivery_pathology.length) {
            result.push('Патологии родов/абортов: ' + _.map(p.delivery_pathology, function (pat) {
                return pat.name;
            }).join(', '))
        }
        if (p.preeclampsia) {
            result.push('Была преэклампсия во время беременности');
        }
        if (p.after_birth_complications && p.after_birth_complications.length) {
            result.push('Осложнения после родов/абортов: ' + _.map(p.after_birth_complications, function (pat) {
                return pat.name;
            }).join(', '))
        }
        return result.join('<br/>')
    };
    var open_edit = function (p) {
        var year_regexp = new RegExp('^[12]\\d{3}$');
        var scope = $scope.$new();
        scope.model = p;
        // Не думайте, что это элегантное решение. Вообще не думайте о нём.
        scope.form_is_invalid = function () {
            return ! (
                year_regexp.test(String(scope.model.year))
                &&
                scope.model.pregnancyResult
                && _.all(scope.model.newborn_inspections, function (inspection) {
                    return (
                        (inspection.alive || inspection.died_at && inspection.died_at.code)
                    )
                })
            )
        };
        scope.add_child = function (pregnancy){
            pregnancy.newborn_inspections.push({
                id: null,
                alive: true,
                deleted: 0
            });
            $timeout(function(){
                $('#childrenTabs').find('a:last').tab('show');
            }, 0);
        };
        scope.delete_child = function(idx) {
            scope.model.newborn_inspections.splice(idx, 1);
            $timeout(function() {
                $('#childrenTabs li.active').removeClass('active');
                $('#childrenTabs').find('a:first').tab('show');
            }, 0);
        };
        scope.result_change = function (pregnancy){
            if (miscarriage_codes.has(pregnancy.pregnancyResult.code)) {
                pregnancy.newborn_inspections = [];
            }
        };
        scope.minYear = moment($scope.header.client.birth_date).year();
        scope.maxYear = new Date().getFullYear();

        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/pregnancies.html',
            scope: scope,
            size: 'lg'
        })
    };

};
var TransfusionsCtrl = function ($scope, $modal, $timeout, RisarApi) {
    $scope.add = function () {
        var model = {};
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.anamnesis.transfusions.save($scope.event_id, result).then(function (result) {
                $scope.anamnesis.transfusions.push(result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        })
    };
    $scope.edit = function (p) {
        var model = angular.extend({}, p);
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.anamnesis.transfusions.save($scope.event_id, result).then(function (result) {
                angular.extend(p, result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        });
    };
    $scope.remove = function (p) {
        if (p.id) {
            RisarApi.anamnesis.transfusions.delete(p.id).then(function () {
                p.deleted = 1;
            });
        } else {
            p.deleted = 1;
        }
    };
    $scope.restore = function (p) {
        if (p.id) {
            RisarApi.anamnesis.transfusions.undelete(p.id).then(function () {
                p.deleted = 0;
            });
        } else {
            p.deleted = 0;
        }
    };

    var open_edit = function (p) {
        var scope = $scope.$new();
        scope.model = p;

        scope.minYear = moment($scope.header.client.birth_date).year();
        scope.maxYear = new Date().getFullYear();
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/transfusions.html',
            scope: scope,
            resolve: {
                model: function () {return p}
            },
            size: 'lg'
        })
    };
};
var IntolerancesCtrl = function ($scope, $modal, $timeout, RisarApi) {
    $scope.intolerance_types = [
        {
            code: 'allergy',
            name: 'Аллергия'
        }, {
            code: 'medicine',
            name: 'Медикаментозная непереносимость'
        }
    ];
    $scope.add = function () {
        var model = {};
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.anamnesis.intolerances.save($scope.client_id, result).then(function (result) {
                $scope.anamnesis.intolerances.push(result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        })
    };
    $scope.edit = function (p) {
        var model = angular.extend({}, p);
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.anamnesis.intolerances.save($scope.client_id, result).then(function (result) {
                angular.extend(p, result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        });
    };
    $scope.remove = function (p) {
        if (p.id) {
            RisarApi.anamnesis.intolerances.delete(p.id, p.type.code).then(function () {
                p.deleted = 1;
            });
        } else {
            p.deleted = 1;
        }
    };
    $scope.restore = function (p) {
        if (p.id) {
            RisarApi.anamnesis.intolerances.undelete(p.id, p.type.code).then(function () {
                p.deleted = 0;
            });
        } else {
            p.deleted = 0;
        }
    };
    var open_edit = function (p) {
        var scope = $scope.$new();
        scope.model = p;
        scope.minDate = $scope.header.client.birth_date;
        scope.maxDate = new Date();

        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/intolerances.html',
            scope: scope,
            resolve: {
                model: function () {return p}
            },
            size: 'lg'
        })
    };
};
var AnamnesisMotherEditCtrl = function ($scope, $controller, $document, $filter, RisarApi, PropsDescriptor, mother_anamnesis_descriptor) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});

    $scope.motherAnamnesisDescriptor = new PropsDescriptor(mother_anamnesis_descriptor);
    $scope.menstruation_min_date = new Date();
    $scope.menstruation_max_date = new Date();

    var reload_anamnesis = function () {
        $scope.reload_header()
            .then(function () {
                $scope.menstruation_min_date = $scope.header.client.birth_date;
            });
        RisarApi.anamnesis.mother.get($scope.event_id)
        .then(function (anamnesis_mother) {
            $scope.anamnesis_mother = anamnesis_mother ? anamnesis_mother : {finished_diseases: [],
                current_diseases: []};
        })
    };
    $scope.$watch('anamnesis_mother.hereditary', function (n, o) {
        if ( n!==o ) {
            var selectedCodes = _.map(n, function(obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ( $filter('intersects')(selectedCodes, ['26']) ) {
                $scope.isHeredTextVisible = true;
            } else {
                $scope.anamnesis_mother.hereditary_defect = null;
                $scope.isHeredTextVisible = false;
            }
        }
    });
    $scope.$watch('anamnesis_mother.fertilization_type', function (n, o) {
        if ( n!==o ) {
            var n = n ? n : [];
            if (safe_traverse(n, ['code']) !== '01') {
                $scope.anamnesis_mother.attempt_number = null;
                $scope.isAttemptVisible = false;
            } else {
                $scope.isAttemptVisible = true;
            }
        }
    });
    angular.forEach(['menstruation_disorders', 'multifetation', 'infertility', 'smoking',
                    'alcohol', 'toxic', 'drugs', 'preeclampsia', 'intrauterine', 'heart_disease'], function(v, _k) {
        $scope.$watch('anamnesis_mother.'+v, function (n, _o) {
            if ($scope.anamnesis_mother) {
                $scope.anamnesis_mother[v] = n === null ? false : $scope.anamnesis_mother[v];
            }
        });
    });

    $scope.save = function () {
        $scope.submit_attempt = true;
        var form = $scope.anamnesisMotherForm;
        if (form.$invalid) {
            var formelm = $('#anamnesisMotherForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        var model = $scope.anamnesis_mother;
        RisarApi.anamnesis.mother.save($scope.event_id, model)
        .then(function (data) {
            $scope.anamnesis_mother = data;
        })
    };
    reload_anamnesis();
};
var AnamnesisUnpregnantEditCtrl = function ($scope, $controller, $document, $filter, RisarApi, PropsDescriptor, gyn_anamnesis_descriptor) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});

    $scope.gynAnamnesisDescriptor = new PropsDescriptor(gyn_anamnesis_descriptor);
    $scope.menstruation_min_date = new Date();
    $scope.menstruation_max_date= new Date();
    

    var reload_anamnesis = function () {
        $scope.reload_header()
            .then(function () {
                $scope.menstruation_min_date = $scope.header.client.birth_date;
            });
        RisarApi.gynecological_anamnesis.general.get($scope.event_id)
        .then(function (data) {
            $scope.anamnesis_unpregnant = data ? data : {
                finished_diseases: [],
                current_diseases: []
            };
        })
    };
    $scope.save = function () {
        $scope.submit_attempt = true;
        var form = $scope.anamnesisUnpregnantForm;
        if (form.$invalid) {
            var formelm = $('#anamnesisUnpregnantForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        var model = $scope.anamnesis_unpregnant;
        RisarApi.gynecological_anamnesis.general.save($scope.event_id, model)
        .then(function (data) {
            $scope.anamnesis_unpregnant = data;
        })
    };
    reload_anamnesis();
    $scope.$watch('anamnesis_unpregnant.hereditary', function (n, o) {
        if ( n!==o ) {
            var selectedCodes = _.map(n, function(obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ( $filter('intersects')(selectedCodes, ['26']) ) {
                $scope.isHeredTextVisible = true;
            } else {
                $scope.anamnesis_unpregnant.hereditary_defect = null;
                $scope.isHeredTextVisible = false;
            }
        }
    });
};
var AnamnesisFatherEditCtrl = function ($scope, $controller, $document, $filter, RisarApi, PropsDescriptor, father_anamnesis_descriptor) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});

    $scope.fatherAnamnesisDescriptor = new PropsDescriptor(father_anamnesis_descriptor);
    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.anamnesis.father.get($scope.event_id)
        .then(function (anamnesis_father) {
            $scope.anamnesis_father = anamnesis_father ? anamnesis_father : {finished_diseases: [],
                current_diseases: []};
        })
    };
    $scope.save = function () {
        var form = $scope.anamnesisFatherForm;
        if (form.$invalid) {
            var formelm = $('#anamnesisFatherForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        var model = $scope.anamnesis_father;
        RisarApi.anamnesis.father.save($scope.event_id, model)
        .then(function (data) {
            $scope.anamnesis_father = data;
        })
    };
    reload_anamnesis();
    $scope.$watch('anamnesis_father.hereditary', function (n, o) {
        if ( n!==o ) {
            var selectedCodes = _.map(n, function(obj, _idx) {
                return safe_traverse(obj, ['code']);
            });
            if ( $filter('intersects')(selectedCodes, ['26']) ) {
                $scope.isHeredTextVisible = true;
            } else {
                $scope.anamnesis_father.hereditary_defect = null;
                $scope.isHeredTextVisible = false;
            }
        }
    });
    angular.forEach(['infertility', 'smoking', 'alcohol', 'toxic', 'drugs', 'HIV'], function(v, _k) {
        $scope.$watch('anamnesis_father.'+v, function (n, _o) {
            if ($scope.anamnesis_father) {
                $scope.anamnesis_father[v] = n === null ? false : $scope.anamnesis_father[v];
            }
        });
    });

};