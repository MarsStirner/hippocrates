/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var AnamnesisCtrl = function ($scope, RisarApi) {
    $scope.hooks = [];
    var tabs = $scope.tabs = {
        motherfather: true,
        pregnancies: false,
        transfusions: false,
        allergies: false
    };

    var params = aux.getQueryParams(window.location.search);
    var hash = window.location.hash;
    if (hash.length > 1) {
        hash = hash.substr(1);
        if (_(tabs).keys().has(hash)) {
            tabs[hash] = true
        }
    }
    var event_id = params.event_id;
    var reload_anamnesis = function () {
        RisarApi.anamnesis(event_id)
        .then(function (anamnesis) {
            $scope.anamnesis = anamnesis;
            $scope.hooks.forEach(function (hook) {hook(anamnesis)});

        })
    };
    reload_anamnesis();
};

var MotherFatherCtrl = function ($scope) {
    $scope.criterions_order = ['education', 'work_group', 'professional_properties', 'infertility',
        'infertility_period', 'infertility_treatment', 'infertility_cause', 'blood_type', 'finished_diseases', 'current_diseases',
        'hereditary', 'bad_habits', 'alcohol', 'smoking', 'toxic', 'drugs'];
    var criterion_names = $scope.criterion_names = {
        'education': 'Образование',
        'work_group': 'Общественно-профессиональная группа',
        'professional_properties': 'Профессиональные и экологические вредности',
        'infertility': 'Бесплодие',
        'infertility_period': 'Длительность',
        'infertility_cause': 'Причина',
        'infertility_treatment': 'Лечение',
        'blood_type': 'Тип крови и резус-фактор',
        'finished_diseases': 'Перенесенные заболевания',
        'current_diseases': 'Текущие заболевания',
        'hereditary': 'Наследственность',
        'bad_habits': 'Вредные привычки',
        'alcohol': 'Алкоголь',
        'smoking': 'Курение',
        'toxic': 'Токсичные вещества',
        'drugs': 'Наркотики'
    };
    $scope.indented = ['infertility_period', 'infertility_treatment', 'infertility_cause', 'alcohol', 'smoking', 'toxic', 'drugs'];
    var reload_hook = function (anamnesis) {
        $scope.warnings = {};
        _(criterion_names).keys().forEach(function (key) {
            if (key == 'blood_type') {
                $scope.warnings[key] = {
                    title: 'Несовместимый резус-фактор'

                };
            } else {
                $scope.warnings[key] = undefined;
            }
        });
    };
    $scope.auto_convert = function (criterion, value) {
        if (_.isUndefined(value))
            return '';
        if (['finished_diseases', 'current_diseases'].has(criterion))
            return '{0} - {1}'.format(value.code, value.name);
        if (criterion == 'blood_type')
            return value.name;
        return value;
    };
    $scope.hooks.push(reload_hook)
};

var PregnanciesCtrl = function ($scope, $modal, $timeout) {
    $scope.add = function () {
        var model = {
            alive: true
        };
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            $scope.anamnesis.pregnancies.push(result);
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
            angular.extend(p, result);
            if (restart) {
                $timeout($scope.add)
            }
        });
    };
    $scope.remove = function (p) {
        p.deleted = true;
    };
    $scope.restore = function (p) {
        p.deleted = false;
    };
    var open_edit = function (p) {
        var scope = $scope.$new();
        scope.model = p;
        return $modal.open({
            templateUrl: '/WebMis20/RISAR/modal/pregnancies.html',
            scope: scope,
            resolve: {
                model: function () {return p}
            },
            size: 'lg'
        })
    };
};

var TransfusionsCtrl = function ($scope, $modal, $timeout) {
    $scope.add = function () {
        var model = {};
        open_edit(model).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            $scope.anamnesis.transfusions.push(result);
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
            angular.extend(p, result);
            if (restart) {
                $timeout($scope.add)
            }
        });
    };
    $scope.remove = function (p) {
        p.deleted = true;
    };
    $scope.restore = function (p) {
        p.deleted = false;
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
