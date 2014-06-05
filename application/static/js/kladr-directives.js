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

                this.register_widget = function(name, w) {
                    widgets[name] = w;
                };

                this.checkValidity = function() {
                    var from_kladr = true;
                    angular.forEach(widgets, function(content, name) {
                        if (content.from_kladr && !content.from_kladr()) {
                            from_kladr = false;
                        }
                    });
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

                $scope.$watch('params.accept_free_input', function(n, o) {
                    if (n !== o) {
                        if (n) {
                            var text = [
                                widgets.locality.hasOwnProperty('name') ? widgets.locality.model.name : widgets.locality.model,
                                'ул. ' + widgets.street.model,
                                'д. ' + widgets.housenumber.model,
                                widgets.corpusnumber.model ? 'к. ' + widgets.corpusnumber.model : '',
                                'кв. ' + widgets.flatnumber.model
                            ].join(', ');
                            widgets.freeinput.model = text;
                            widgets.locality.onFreeInputStateChanged(true);
                        } else {
                            widgets.freeinput.model = '';
                            widgets.locality.onFreeInputStateChanged(false);
                        }
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
            require: '^form',
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
            link: function(scope, elm, attrs, formCtrl) {
                scope.addressForm = formCtrl;
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
                $scope.getCity = function(val) {
                    return $http.get(url_kladr_get, {
                        params: {
                            city: val
                        }
                    }).then(function(res) {
                        $scope.items = res.data.result;
                        return $scope.items;
                    });
                };

                $scope.from_kladr = function(value) {
                    return $scope.items.indexOf($scope.model) !== -1;
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrctrl = ctrls[0],
                    modelctrl = ctrls[1];
                scope.items = [];
                kladrctrl.register_widget('locality', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
                scope.onChanged = function() {
                    kladrctrl.checkValidity();
                };
                scope.onFreeInputStateChanged = function(enabled) {
                    if (enabled) {
                        scope.prev_validity = modelctrl.$valid;
                        modelctrl.$setValidity('addr_from_kladr', true);
                    } else {
                        modelctrl.$setValidity('addr_from_kladr', scope.prev_validity !== undefined ? scope.prev_validity : true);
                    }
                };
                scope.$watch('model', function(n, o) {
                    if (o === undefined && n !== undefined) {
                        // первичная инициализация, необходимо для правильной установки free_input_mode после загрузки
                        scope.items = [n];
                    } else if (n && n !== o) {
                        scope.onChanged();

                        if (!modelctrl.$isEmpty(n) && !scope.from_kladr(n)) {
                            modelctrl.$setValidity('addr_from_kladr', false);
                        } else {
                            modelctrl.$setValidity('addr_from_kladr', true);
                        }
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
                kladrctrl.register_widget('locality_type', scope);
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
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            controller: function($scope) {
                $scope.getStreet = function(val) {
                    return $http.get(url_kladr_get, {
                        params: {
                            city: $scope.getSelectedLocation(),
                            street: val
                        }
                    }).then(function(res) {
                        $scope.items = res.data.result;
                        return $scope.items;
                    });
                };

                $scope.from_kladr = function() {
                    return true;//$scope.items.indexOf($scope.model) !== -1;
                };
            },
            link: function(scope, elm, attrs, kladrctrl) {
                scope.items = [];
                kladrctrl.register_widget('street', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.inputStarted = kladrctrl.inputStarted;
                scope.getSelectedLocation = function() {
                    return kladrctrl.getLocation().code;
                };
                scope.onChanged = function() {
                    kladrctrl.checkValidity();
                };
                scope.$watch('model', function(n, o) {
                    if (n && n !== o) {
                        scope.onChanged();
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
                kladrctrl.register_widget('housenumber', scope);
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
                kladrctrl.register_widget('corpusnumber', scope);
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
                kladrctrl.register_widget('flatnumber', scope);
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
                kladrctrl.register_widget('freeinput', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
            },
            template: '<textarea class="form-control" rows="3" autocomplete="off" placeholder="Адрес в свободном виде" ' +
                      'ng-model="model" ng-required="inFreeInputMode()" ng-show="true"></textarea>'
        }
    }])
;