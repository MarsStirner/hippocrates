'use strict';

angular.module('WebMis20.kladrDirectives', ['ui.bootstrap']).
    directive('wmKladrAddress', [function () {
        return {
            restrict: 'E',
            transclude: true,
            scope: { },
            controller: function ($scope) {
                var widgets = $scope.widgets = {};
                var params = $scope.params = {};
                params.free_input_mode = false;
                params.accept_free_input = false;

                this.inFreeInputMode = function() {
                    return params.accept_free_input;
                };

                this.registerWidget = function(name, w) {
                    widgets[name] = w;
                };

                this.checkValidity = function() {
                    var from_kladr = true;
                    if (!widgets.locality.from_kladr() || !widgets.street.from_kladr()) {
                        from_kladr = false;
                    }
                    params.free_input_mode = !from_kladr;
                };

                this.inputStarted = function() {
                    var started = false;
                    angular.forEach(widgets, function(content, name) {
                        if (name !== 'freeinput' && content.model) {
                            started = true;
                        }
                    });
                    return started;
                };

                this.getLocation = function() {
                    return widgets.locality.model;
                };

                this.clearStreet = function() {
                    widgets.street.model = undefined;
                }

                $scope.setFreeInputText = function(accepted) {
                    var text = '';
                    if (accepted) {
                        var locality_model = widgets.locality.model,
                            street_model = widgets.street.model;
                        text = [
                            locality_model.hasOwnProperty('name') ? locality_model.name : locality_model,
                            street_model.hasOwnProperty('name') ? street_model.name : street_model,
                            'д. ' + widgets.housenumber.model,
                            widgets.corpusnumber.model ? 'к. ' + widgets.corpusnumber.model : '',
                            'кв. ' + widgets.flatnumber.model
                        ].join(', ');
                    }
                    widgets.freeinput.model = text;
                    widgets.locality.onFreeInputStateChanged(accepted);
                    widgets.street.onFreeInputStateChanged(accepted);
                };

                $scope.$watch('params.accept_free_input', function(n, o) {
                    if (n !== o) {
                        $scope.setFreeInputText(n);
                    }
                });
            },
            template: '<alert ng-show="params.free_input_mode" type="danger">Введенный адрес не найден в справочнике адресов Кладр. ' +
                      '<a ng-click="params.accept_free_input = !params.accept_free_input">' +
                      '[[params.accept_free_input ? "Выбрать из Кладр" : "Ввести адрес вручную?"]]</alert>' +
                      '<div ng-transclude></div>'
        };
    }]).
    directive('wmKladrBaseLayout', [function() {
        return {
            restrict: 'E',
            require: ['^wmKladrAddress', '^form'],
            transclude: true,
            scope: {
                prefix: '@',
                localityModel: '=',
                localityTypeModel: '=',
                streetModel: '=',
                houseModel: '=',
                corpusModel: '=',
                flatModel: '=',
                freeInputModel: '='
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    formCtrl = ctrls[1];
                scope.addressForm = formCtrl;
                scope.inFreeInputMode = kladrCtrl.inFreeInputMode;
            },
            templateUrl: 'kladr-ui.html'
        };
    }]).
    directive('wmKladrLocality', ['$http', function($http) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            controller: function($scope) {
                $scope.getCity = function(search_q) {
                    var url = [kladr_city + 'search/' + search_q + '/'].join('');
                    return $http.get(url, {}).then(function(res) {
                        $scope.items = res.data.result;
                        return $scope.items;
                    });
                };

                $scope.from_kladr = function() {
                    return $scope.items.filter(function(item) {
                        return angular.equals(item, $scope.model);
                    }).length;
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                scope.items = [];
                kladrCtrl.registerWidget('locality', scope);
                scope.inFreeInputMode = kladrCtrl.inFreeInputMode;
                scope.inputStarted = kladrCtrl.inputStarted;

                scope.onFreeInputStateChanged = function(enabled) {
                    if (enabled) {
                        scope.prev_validity = modelctrl.$valid;
                        modelCtrl.$setValidity('addrFromKladr', true);
                    } else {
                        modelCtrl.$setValidity('addrFromKladr', scope.prev_validity !== undefined ? scope.prev_validity : true);
                    }
                };
                scope.$watch('model', function(n, o) {
                    if (o === undefined && n !== undefined) {
                        // первичная инициализация, необходимо для правильной установки free_input_mode после загрузки
                        scope.items = [n];
                    } else if (n && n !== o) {
                        kladrCtrl.checkValidity();

                        if (!modelCtrl.$isEmpty(n) && !scope.from_kladr(n)) {
                            modelCtrl.$setValidity('addrFromKladr', false);
                        } else {
                            modelCtrl.$setValidity('addrFromKladr', true);
                            kladrCtrl.clearStreet();
                        }
                    } else {
                        kladrCtrl.clearStreet();
                    }
                });
            },
            // todo: evaluate name in compile ?
            template: '<input type="text" class="form-control"' +
                      'autocomplete="off" placeholder="Населенный пункт"' +
                      'ng-model="model" typeahead="city as city.name for city in getCity($viewValue)"' +
                      'typeahead-wait-ms="1000" typeahead-min-length="2"' +
                      'ng-required="inputStarted() && !inFreeInputMode()" ng-disabled="inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrLocalityType', ['RefBookService', function(RefBookService) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
//            controller: function($scope) {
//                $scope.rbLocalityType = RefBookService.get('LocalityType');
//            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrctrl = ctrls[0],
                    modelctrl = ctrls[1];
                scope.rbLocalityType = RefBookService.get('LocalityType');
                kladrctrl.registerWidget('locality_type', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;

                modelctrl.$parsers.unshift(function(viewValue) {
                    if (modelctrl.$isEmpty(viewValue)) {
                        modelctrl.$setValidity('select', false);
                        return undefined;
                    }
                    modelctrl.$setValidity('select', true);
                    return viewValue;
                });
            },
            template: '<select class="form-control" ng-model="model" ' +
                      'ng-options="item as item.name for item in rbLocalityType.objects track by item.id" ' +
                      'ng-required="inputStarted() && !inFreeInputMode()" ng-disabled="inFreeInputMode()">' +
                      '<option value="">Не выбрано</option>' +
                      '</select>'
        }
    }]).
    directive('wmKladrStreet', ['$http', function($http) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            controller: function($scope) {
                $scope.getStreet = function(search_q) {
                    var url = [kladr_street, 'search/', $scope.getSelectedLocation(), '/', search_q, '/' ].join('');
                    return $http.get(url, {}).then(function(res) {
                        $scope.items = res.data.result;
                        return $scope.items;
                    });
                };

                $scope.from_kladr = function() {
                    return $scope.items.filter(function(item) {
                        return angular.equals(item, $scope.model);
                    }).length;
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrctrl = ctrls[0],
                    modelctrl = ctrls[1];
                scope.items = [];
                kladrctrl.registerWidget('street', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
                scope.getSelectedLocation = function() {
                    return kladrctrl.getLocation().code;
                };

                scope.onFreeInputStateChanged = function(enabled) {
                    if (enabled) {
                        scope.prev_validity = modelctrl.$valid;
                        modelctrl.$setValidity('addrFromKladr', true);
                    } else {
                        modelctrl.$setValidity('addrFromKladr', scope.prev_validity !== undefined ? scope.prev_validity : true);
                    }
                };
                scope.$watch('model', function(n, o) {
                    if (o === undefined && n !== undefined) {
                        // первичная инициализация, необходимо для правильной установки free_input_mode после загрузки
                        scope.items = [n];
                    } else if (n && n !== o) {
                        kladrctrl.checkValidity();

                        if (!modelctrl.$isEmpty(n) && !scope.from_kladr(n)) {
                            modelctrl.$setValidity('addrFromKladr', false);
                        } else {
                            modelctrl.$setValidity('addrFromKladr', true);
                        }
                    }
                });
            },
            template: '<input type="text" class="form-control"' +
                      'autocomplete="off" placeholder="Улица"' +
                      'ng-model="model" typeahead="street as street.name for street in getStreet($viewValue)"' +
                      'typeahead-wait-ms="1000" typeahead-min-length="2"' +
                      'ng-required="inputStarted() && !inFreeInputMode()" ng-disabled="inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrHouseNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('housenumber', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model" ng-required="inputStarted() && !inFreeInputMode()"' +
                      'ng-disabled="inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrCorpusNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('corpusnumber', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model" ng-disabled="inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrFlatNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('flatnumber', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model" ng-required="inputStarted() && !inFreeInputMode()"' +
                      'ng-disabled="inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrFreeInput', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            controller: function($scope) {
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('freeinput', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
            },
            template: '<textarea class="form-control" rows="3" autocomplete="off" placeholder="Адрес в свободном виде" ' +
                      'ng-model="model" ng-required="inFreeInputMode()"></textarea>'
        }
    }])
;