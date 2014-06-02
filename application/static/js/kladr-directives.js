'use strict';

angular.module('WebMis20.kladrDirectives', ['ui.bootstrap']).
    directive('wmKladrAddress', [function () {
        return {
            restrict: 'E',
            transclude: true,
            scope: {

            },
            controller: function ($scope) {
                var widgets = $scope.widgets = {};
                var params = $scope.params = {};
                params.free_input_mode = false;
                params.accept_free_input = false;

                this.inFreeInputMode = function() {
                    return params.free_input_mode;
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

                this.getLocation = function() {
                    return widgets.location.model;
                };

                $scope.$watch('params.accept_free_input', function(n, o) {
                    if (n !== o) {
                        if (n) {
                            var text = widgets.locality.model;
                            widgets.freeinput.model = text;
                        } else {
                            widgets.freeinput.model = '';
                        }
                    }
                });

            },
//            link: function(scope, elm, attrs) {
//            },
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
                korpusModel: '=',
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
            require: '^wmKladrAddress',
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

                $scope.from_kladr = function() {
                    return $scope.items.indexOf($scope.model) !== -1;
                };
            },
            link: function(scope, elm, attrs, kladrctrl) {
                scope.items = [];
                kladrctrl.register_widget('locality', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
                scope.onChanged = function() {
                    kladrctrl.checkValidity();
                };
                scope.$watch('model', function(n, o) {
                    if (n && n !== o) {
                        scope.onChanged();
                    }
                });
            },
            // todo: evaluate name in compile
            template: '<input type="text" class="form-control"' +
                      'autocomplete="off" placeholder="Населенный пункт"' +
                      'ng-model="model" typeahead="city as city.name for city in getCity($viewValue)"' +
                      'typeahead-wait-ms="1000" typeahead-min-length="2"' +
                      'ng-required="!inFreeInputMode()" />'
        }
    }]).
    directive('wmKladrLocalityType', ['RefBookService', function(RefBookService) {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
//            controller: function($scope) {
//                $scope.rbLocalityType = RefBookService.get('LocalityType');
//            },
            link: function(scope, elm, attrs, kladrctrl) {
                scope.rbLocalityType = RefBookService.get('LocalityType');
                kladrctrl.register_widget('locality_type', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
            },
            template: '<select class="form-control" ng-model="model" ' +
                      'ng-options="item as item.name for item in rbLocalityType.objects track by item.id" ' +
                      'ng-required="true">' +
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
                    return $scope.items.indexOf($scope.model) !== -1;
                };
            },
            link: function(scope, elm, attrs, kladrctrl) {
                scope.items = [];
                kladrctrl.register_widget('street', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
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
            // todo: evaluate name in compile
            template: '<input type="text" class="form-control"' +
                      'autocomplete="off" placeholder="Улица"' +
                      'ng-model="model" typeahead="street as street.name for city in getStreet($viewValue)"' +
                      'typeahead-wait-ms="1000" typeahead-min-length="2"' +
                      'ng-required="!inFreeInputMode()" />'
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
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model" ng-required="!inFreeInputMode()"/>'
        }
    }]).
    directive('wmKladrKorpusNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.register_widget('korpusnumber', scope);
                scope.inFreeInputMode = kladrctrl.inFreeInputMode;
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model"/>'
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
            },
            template: '<input type="text" class="form-control" autocomplete="off"' +
                      'ng-model="model" ng-required="!inFreeInputMode()"/>'
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