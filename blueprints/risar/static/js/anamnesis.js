/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var AnamnesisCtrl = function ($scope, RisarApi) {
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
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    var reload_anamnesis = function () {
        RisarApi.anamnesis(event_id)
        .then(function (anamnesis) {
            $scope.anamnesis = anamnesis;
            $scope.warnings = calculate_warnings(anamnesis);
        })
    };
    var calculate_warnings = function (anamnesis) {
        var warnings = {};
        _(criterion_names).keys().forEach(function (key) {
            warnings[key] = key == 'rh';
        });
        return warnings;
    };
    reload_anamnesis();
};
