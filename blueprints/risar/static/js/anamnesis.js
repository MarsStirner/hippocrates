/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var AnamnesisCtrl = function ($scope, RisarApi) {
    $scope.hooks = [];

    var params = aux.getQueryParams(window.location.search);
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
        'infertility_period', 'infertility_cause', 'blood_type', 'rh', 'finished_diseases', 'current_diseases',
        'hereditary', 'alcohol', 'smoking', 'toxic', 'drugs'];
    var criterion_names = $scope.criterion_names = {
        'education': 'Образование',
        'work_group': 'Общественно-профессиональная группа',
        'professional_properties': 'Профессиональные и экологические особенности',
        'infertility': 'Бесплодие',
        'infertility_period': 'Длительность бесплодия',
        'infertility_cause': 'Причина бесплодия',
        'blood_type': 'Тип крови',
        'rh': 'Резус-фактор',
        'finished_diseases': 'Перенесенные заболевания',
        'current_diseases': 'Текущие заболевания',
        'hereditary': 'Наследственность',
        'alcohol': 'Алкоголь',
        'smoking': 'Курение',
        'toxic': 'Токсичные вещества',
        'drugs': 'Наркотики'
    };
    var reload_hook = function (anamnesis) {
        $scope.warnings = {};
        _(criterion_names).keys().forEach(function (key) {
            if (key == 'rh') {
                $scope.warnings[key] = 'Несовместимый резус-фактор';
            } else {
                $scope.warnings[key] = undefined;
            }
        });
    };
    $scope.hooks.push(reload_hook)
};

var PregnanciesCtrl = function ($scope, $modal) {
    $scope.add = function () {
        var model = {
            alive: true
        };
        open_edit(model).result.then(function (result) {
            $scope.anamnesis.pregnancies.push(result)
        })
    };
    $scope.edit = function (p) {
        var model = angular.extend({}, p);
        open_edit(model).result.then(function (result) {
            angular.extend(p, result);
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

var TransfusionsCtrl = function ($scope, $modal) {
    $scope.add = function () {
        var model = {};
        open_edit(model).result.then(function (result) {
            $scope.anamnesis.transfusions.push(result)
        })
    };
    $scope.edit = function (p) {
        var model = angular.extend({}, p);
        open_edit(model).result.then(function (result) {
            angular.extend(p, result);
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
