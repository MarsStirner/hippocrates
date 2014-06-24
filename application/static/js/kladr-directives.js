'use strict';

angular.module('WebMis20.kladrDirectives', ['ui.bootstrap']).
    directive('wmKladrAddress', ['$timeout', function($timeout) {
        return {
            restrict: 'E',
            require: '^form',
            scope: {
                prefix: '@',
                localityModel: '=',
                localityTypeModel: '=',
                streetModel: '=',
                houseModel: '=',
                corpusModel: '=',
                flatModel: '=',
                freeInputModel: '=',
                addressModel: '=',
                editMode: '&',
                copyFromModel: '='
            },
            controller: function ($scope) {
                var widgets = $scope.widgets = {};
                var mode = $scope.mode = {};
                mode.kladr_addr_valid = false;
                mode.switch_to_free_input = false;

                this.registerWidget = function(name, w) {
                    widgets[name] = w;
                };

                $scope.inFreeInputMode = function() {
                    return mode.switch_to_free_input;
                };

                $scope.setFreeInputText = function(switched) {
                    var text = '';
                    if (switched) {
                        text = [
                            widgets.locality.getText(),
                            widgets.street.getText(),
                            'д. ' + (widgets.housenumber.model || '') + (widgets.corpusnumber.model ?
                                                                         'к. ' + widgets.corpusnumber.model : ''),
                            'кв. ' + (widgets.flatnumber.model || '')
                        ].join(', ');
                    }
                    widgets.freeinput.model = text;
                };

                this.getLocation = function() {
                    return widgets.locality.model;
                };

                $scope.clearStreet = function() {
                    widgets.street.reset();
                };

                $scope.copy_address = function(same) {
                    var cur_id = $scope.addressModel.id;
                    if (same) {
                        var copy_from = $scope.copyFromModel;
                        if (copy_from.free_input) {
                            mode.switch_to_free_input = true;
                        }
                        angular.copy(copy_from, $scope.addressModel);
                        $scope.addressModel.id = cur_id;
                        // если что-то изменится в совпадающем адресе, то убрать галочку и прекратить слежение
                        // timeout - чтобы сначала прошли предыдущие watch со смены $scope.addressModel
                        $timeout(function() {
                            var unregister_watcher = $scope.$watchCollection(function() {
                                var col = [];
                                angular.forEach(widgets, function(w) {
                                    col.push(w.model);
                                });
                                return col;
                            }, function(n, o) {
                                if (n !== o) {
                                    $scope.addressModel.same_as_reg = false;
                                    unregister_watcher();
                                }
                            });
                        });
                    } else {
                        var copy_from = {};
                        mode.switch_to_free_input = false;
                        angular.copy(copy_from, $scope.addressModel);
                    }
                    $scope.addressModel.same_as_reg = same;
                    $scope.addressModel.copy_from_id = copy_from.id;
                };
            },
            link: function(scope, elm, attrs, formCtrl) {
                scope.addressForm = formCtrl;

                scope.$watchCollection(function() {
                    return [scope.widgets.locality.model, scope.widgets.street.model];
                }, function(n, o) {
                    scope.mode.kladr_addr_valid = n.filter(function(model) {
                        return angular.isDefined(model);
                    }).length === n.length;
                });
                var unregister_init_mode_set = scope.$watch('widgets.freeinput.model', function(n, o) {
                    if (angular.isString(n) && n !== '') {
                        scope.mode.switch_to_free_input = true;
                        unregister_init_mode_set();
                    }
                });
                scope.$watch('mode.switch_to_free_input', function(n, o) {
                    if (n !== o) {
                        scope.setFreeInputText(n);
                        scope.$broadcast('switch_to_freeinput', n);
                    }
                });
                scope.$watch('addressForm.$dirty', function(n, o) {
                    if (n !== o) {
                        scope.addressModel.dirty = n;
                    }
                });
                scope.$watch(function() {
                    return scope.widgets.locality.getText();
                }, function(n, o) {
                    if (n !== o && o) { scope.clearStreet(); }
                });
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
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.getCity = function(search_q) {
                    var url = [kladr_city + 'search/' + search_q + '/'].join('');
//                    var url = url_kladr_get;
                    return $http.get(url, {}).then(function(res) {
                        return res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                kladrCtrl.registerWidget('locality', scope);

                scope.getText = function() {
                    return modelCtrl.$viewValue;
                };
                scope.reset =  function() {
                    scope.model = undefined;
                };

                scope.$on('switch_to_freeinput', function(event, on) {
                    modelCtrl.$setValidity('editable', on);
                });
            },
            template:
                '<input type="text" class="form-control" placeholder="" autocomplete="off"\
                    ng-model="model" typeahead="city as city.name for city in getCity($viewValue)"\
                    typeahead-wait-ms="1000" typeahead-min-length="2" typeahead-editable="false"\
                    ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrLocalityType', ['RefBookService', function(RefBookService) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                scope.rbLocalityType = RefBookService.get('LocalityType');
                kladrCtrl.registerWidget('locality_type', scope);

                modelCtrl.$parsers.unshift(function(viewValue) {
                    if (modelCtrl.$isEmpty(viewValue)) {
                        modelCtrl.$setValidity('select', false);
                        return undefined;
                    }
                    modelCtrl.$setValidity('select', true);
                    return viewValue;
                });
            },
            template:
                '<select class="form-control" ng-model="model"\
                    ng-options="item as item.name for item in rbLocalityType.objects track by item.id"\
                    ng-required="required" ng-disabled="disabled">\
                    <option value="">Не выбрано</option>\
                 </select>'
        }
    }]).
    directive('wmKladrStreet', ['$http', function($http) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.getStreet = function(search_q) {
                    var loc = $scope.getSelectedLocation();
                    if (!loc) {
                        return [];
                    }
                    var url = [kladr_street, 'search/', loc, '/', search_q, '/' ].join('');
                    return $http.get(url, {}).then(function(res) {
                        return res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                kladrCtrl.registerWidget('street', scope);

                scope.getSelectedLocation = function() {
                    var loc = kladrCtrl.getLocation();
                    return loc ? loc.code : undefined;
                };
                scope.getText = function() {
                    return modelCtrl.$viewValue;
                };
                scope.reset =  function() {
                    scope.model = undefined;
                    modelCtrl.$setViewValue('');
                    modelCtrl.$render();
                };

                scope.$on('switch_to_freeinput', function(event, on) {
                    modelCtrl.$setValidity('editable', on);
                });
            },
            template:
                '<input type="text" class="form-control" autocomplete="off" placeholder=""\
                    ng-model="model" typeahead="street as street.name for street in getStreet($viewValue)"\
                    typeahead-wait-ms="1000" typeahead-min-length="2" typeahead-editable="false"\
                    ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrHouseNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('housenumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrCorpusNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('corpusnumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrFlatNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('flatnumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrFreeInput', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
            },
            link: function(scope, elm, attrs, kladrCtrl) {
                kladrCtrl.registerWidget('freeinput', scope);
            },
            template:
                '<textarea class="form-control" rows="3" autocomplete="off" placeholder="Адрес в свободном виде"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"></textarea>'
        }
    }])
;