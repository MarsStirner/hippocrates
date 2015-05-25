/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var AnamnesisCtrl = function ($scope, RisarApi, RefBookService) {
    $scope.hooks = [];
    $scope.rbDiagnosisType = RefBookService.get('rbDiagnosisType');
    $scope.menstruation_max_date= new Date();
    $scope.menstruation_max_date.setDate($scope.menstruation_max_date.getDate() - 1);
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
        .then(function (event) {
            $scope.chart = event;
            $scope.client_id = event.client.id;
            $scope.hooks.forEach(function (hook) {hook(event)});
        })
    };
    reload_anamnesis();
};

var MotherFatherCtrl = function ($scope) {
    var reload_hook = function (chart) {
        $scope.warnings = {
            blood_type: 'Несовместимый резус-фактор'
        };
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
var AnamnesisMotherEditCtrl = function ($scope, $document, RisarApi) {
    $scope.hooks.push(function (chart) {
        if (!chart.anamnesis.mother) {
            chart.anamnesis.mother = {finished_diseases: [],
                                      current_diseases: []};
        }
    });
    $scope.save = function () {
        $scope.submit_attempt = true;
        var form = $scope.anamnesisMotherForm;
        if (form.$invalid) {
            var formelm = $('#anamnesisMotherForm').find('.ng-invalid:not(ng-form):first');
            $document.scrollToElement(formelm, 100, 1500);
            return false;
        }
        var model = $scope.chart.anamnesis.mother;
        RisarApi.anamnesis.mother.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.anamnesis.mother = data;
        })
    }
};
var AnamnesisFatherEditCtrl = function ($scope, RisarApi) {
    $scope.hooks.push(function (chart) {
        if (!chart.anamnesis.father) {
            chart.anamnesis.father = {finished_diseases: [],
                                      current_diseases: []};
        }
    });
    $scope.save = function () {
        var model = $scope.chart.anamnesis.father;
        RisarApi.anamnesis.father.save($scope.chart.id, model)
        .then(function (data) {
            $scope.chart.anamnesis.father = data;
        })
    }
};