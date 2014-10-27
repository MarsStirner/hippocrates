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
        intolerances: false
    };

    var params = aux.getQueryParams(window.location.search);
    var hash = window.location.hash;
    if (hash.length > 1) {
        hash = hash.substr(1);
        if (_(tabs).keys().has(hash)) {
            tabs[hash] = true
        }
    }
    var event_id = $scope.event_id = params.event_id;
    var reload_anamnesis = function () {
        RisarApi.chart.get(event_id)
        .then(function (data) {
            $scope.chart = data.event;
            $scope.client_id = data.event.client.id;
            $scope.hooks.forEach(function (hook) {hook(data.event)});
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
    var reload_hook = function (chart) {
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
var PregnanciesCtrl = function ($scope, $modal, $timeout, RisarApi) {
    $scope.add = function () {
        var model = {
            alive: true
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
var AnamnesisMotherEditCtrl = function ($scope, RisarApi, RefBook) {
    $scope.hooks.push(function (chart) {
        if (!chart.anamnesis.mother) {
            chart.anamnesis.mother = {};
        }
    });
    $scope._isArray = _.isArray;
    var criterions = $scope.criterions = [
        'education', 'work_group', 'professional_properties', 'family_income', 'blood_type',
        'menstruation', [
            'menstruation_start_age',
            'menstruation_duration',
            'menstruation_period',
            'menstruation_disorders'
        ], 'sex_life_start_age', 'contraception_type', 'natural_pregnancy', 'multifetation',
        'infertility', [
            'intertility_type',
            'infertility_period',
            'infertility_treatment',
            'infertility_cause'
        ], 'finished_diseases', 'hereditary', 'current_diseases',
        'bad_habits', [
            'alcohol', 'smoking', 'toxic', 'drugs'
        ]
    ];
    $scope.MKB = new RefBook('MKB');
    $scope.meta = {
        education: {title: 'Образование', type: 'rb', rb: 'rbRisarEducation'},
        work_group: {title: 'Общественно-профессиональная группа', type: 'rb', rb: 'rbRisarWorkGroup'},
        professional_properties: {title: 'Профессиональные вредности', type: 'str'},
        family_income: {title: 'Доход семьи', type: 'str'},
        blood_type: {title: 'Группа крови', type: 'rb', rb: 'rbBloodType'},
        menstruation: {title: 'Менструации'},
        menstruation_start_age: {title: 'с возраста', type: 'num'},
        menstruation_duration: {title: 'длительность', type: 'num'},
        menstruation_period: {title: 'продолжительность цикла', type: 'num'},
        menstruation_disorders: {title: 'нарушения', type: 'chk'},
        sex_life_start_age: {title: 'Половая жизнь с', type: 'num'},
        contraception_type: {title: 'Тип контрацепции', type: 'str'},
        natural_pregnancy: {title: 'Беременность наступила естественным путём', type: 'chk'},
        multifetation: {title: 'Многоплодие', type: 'chk'},
        infertility: {title: 'Бесплодие', type: 'chk'},
        infertility_type: {title: 'вид', type: 'str'},
        infertility_period: {title: 'длительность', type: 'num'},
        infertility_treatment: {title: 'лечение', type: 'str'},
        infertility_cause: {title: 'причина', type: 'str'},
        finished_diseases: {title: 'перенесенные заболевания', type: 'mkb-multi'},
        hereditary: {title: 'Наследственность', type: 'str'},
        current_diseases: {title: 'Текущие заболевания', type: 'mkb-multi'},
        bad_habits: {title: 'Вредные привычки'},
        alcohol: {title: 'Алкоголь', type: 'chk'},
        smoking: {title: 'Курение', type: 'chk'},
        toxic: {title: 'Токсические вещества', type: 'chk'},
        drugs: {title: 'Наркотики', type: 'chk'}
    };
    $scope.save = function () {
        var model = $scope.chart.anamnesis.mother;
        RisarApi.anamnesis.mother.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.anamnesis.mother = data;
        })
    }
};
var AnamnesisFatherEditCtrl = function ($scope, RisarApi, RefBook) {
    $scope.hooks.push(function (chart) {
        if (!chart.anamnesis.father) {
            chart.anamnesis.father = {};
        }
    });
    $scope._isArray = _.isArray;
    var criterions = $scope.criterions = [
        'name', 'education', 'work_group', 'professional_properties', 'blood_type',
        'phone', 'HIV',
        'infertility', [
            'intertility_type',
            'infertility_period',
            'infertility_treatment',
            'infertility_cause'
        ], 'finished_diseases', 'hereditary', 'current_diseases',
        'bad_habits', [
            'alcohol', 'smoking', 'toxic', 'drugs'
        ]
    ];
    $scope.MKB = new RefBook('MKB');
    $scope.meta = {
        name: {title: 'ФИО', type: 'str'},
        education: {title: 'Образование', type: 'rb', rb: 'rbRisarEducation'},
        work_group: {title: 'Общественно-профессиональная группа', type: 'rb', rb: 'rbRisarWorkGroup'},
        professional_properties: {title: 'Профессиональные вредности', type: 'str'},
        blood_type: {title: 'Группа крови', type: 'rb', rb: 'rbBloodType'},
        phone: {title: 'Телефон', type: 'str'},
        HIV: {title: 'ВИЧ', type: 'chk'},
        infertility: {title: 'Бесплодие', type: 'chk'},
        infertility_type: {title: 'вид', type: 'str'},
        infertility_period: {title: 'длительность', type: 'num'},
        infertility_treatment: {title: 'лечение', type: 'str'},
        infertility_cause: {title: 'причина', type: 'str'},
        finished_diseases: {title: 'перенесенные заболевания', type: 'mkb-multi'},
        hereditary: {title: 'Наследственность', type: 'str'},
        current_diseases: {title: 'Текущие заболевания', type: 'mkb-multi'},
        bad_habits: {title: 'Вредные привычки'},
        alcohol: {title: 'Алкоголь', type: 'chk'},
        smoking: {title: 'Курение', type: 'chk'},
        toxic: {title: 'Токсические вещества', type: 'chk'},
        drugs: {title: 'Наркотики', type: 'chk'}
    };
    $scope.save = function () {
        var model = $scope.chart.anamnesis.father;
        RisarApi.anamnesis.father.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.anamnesis.father = data;
        })
    }
};