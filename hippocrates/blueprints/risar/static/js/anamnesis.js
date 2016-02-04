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
        RisarApi.chart.get_header($scope.event_id).
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

var AnamnesisCtrl = function ($scope, $controller, RisarApi) {
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
    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.anamnesis.get($scope.event_id)
        .then(function (data) {
            $scope.client_id = data.client_id;
            $scope.anamnesis = data.anamnesis;
        })
    };
    reload_anamnesis();
};

var MotherFatherCtrl = function ($scope) {
    $scope.warnings = {
        blood_type: 'Несовместимый резус-фактор'
    };
};
var PregnanciesCtrl = function ($scope, $modal, $timeout, RisarApi) {
    $scope.add = function () {
        var model = {
            newborn_inspections: []
        };
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.anamnesis.pregnancies.save($scope.event_id, result).then(function (result) {
                $scope.chart.anamnesis.pregnancies.push(result);
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
            RisarApi.anamnesis.pregnancies.save($scope.event_id, result).then(function (result) {
                angular.extend(p, result);
            });
            if (restart) {
                $timeout($scope.add)
            }
        });
    };

    $scope.add_child = function (pregnancy){
        pregnancy.newborn_inspections.push({});
        $timeout(function(){
            $('#childrenTabs').find('a:last').tab('show');
        }, 0);

    };

    $scope.result_change = function (pregnancy){
        if (['med_abortion12', 'med_abortion', 'misbirth11', 'misbirth21', 'misbirth'].indexOf(pregnancy.pregnancyResult.code) > -1){
            pregnancy.newborn_inspections = pregnancy.newborn_inspections.filter(function(inspection){
                inspection.deleted = 1;
                return inspection.id
            })
        }
    };

    $scope.remove = function (p) {
        if (p.id) {
            RisarApi.anamnesis.pregnancies.delete(p.id).then(function () {
                p.deleted = 1;
            });
        } else {
            p.deleted = 1;
        }
    };
    $scope.restore = function (p) {
        if (p.id) {
            RisarApi.anamnesis.pregnancies.undelete(p.id).then(function () {
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
        result.push('масса: ' + child.weight);
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
        if (p.maternity_aid) {
            result.push('Пособия, операции: ' + p.maternity_aid.name)
        }
        if (p.pregnancy_pathologies && p.pregnancy_pathologies.length) {
            result.push('патологии беременности: ' + _.map(p.pregnancy_pathologies, function (pat) {
                return pat.name;
            }).join(', '))
        }
        if (p.delivery_pathologies && p.delivery_pathologies.length) {
            result.push('Патологии родов/абортов: ' + _.map(p.delivery_pathologies, function (pat) {
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
                && _.all(scope.model.newborn_inspections, function (inspection) {
                    return (
                        (inspection.alive || inspection.died_at && inspection.died_at.code)
                        && _.isFinite(inspection.weight)
                    )
                })
            )
        };
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
                $scope.chart.anamnesis.transfusions.push(result);
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
                $scope.chart.anamnesis.intolerances.push(result);
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
var AnamnesisMotherEditCtrl = function ($scope, $controller, $document, RisarApi) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});

    $scope.menstruation_max_date= new Date();
    $scope.menstruation_max_date.setDate($scope.menstruation_max_date.getDate() - 1);

    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.anamnesis.mother.get($scope.event_id)
        .then(function (anamnesis_mother) {
            $scope.anamnesis_mother = anamnesis_mother ? anamnesis_mother : {finished_diseases: [],
                current_diseases: []};
        })
    };
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
var AnamnesisFatherEditCtrl = function ($scope, $controller, RisarApi) {
    $controller('AnamnesisBaseCtrl', {$scope: $scope});
    var reload_anamnesis = function () {
        $scope.reload_header();
        RisarApi.anamnesis.father.get($scope.event_id)
        .then(function (anamnesis_father) {
            $scope.anamnesis_father = anamnesis_father ? anamnesis_father : {finished_diseases: [],
                current_diseases: []};
        })
    };
    $scope.save = function () {
        var model = $scope.anamnesis_father;
        RisarApi.anamnesis.father.save($scope.event_id, model)
        .then(function (data) {
            $scope.anamnesis_father = data;
        })
    };
    reload_anamnesis();
};