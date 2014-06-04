'use strict';

angular.module('WebMis20.directives', ['ui.bootstrap', 'ui.select', 'ngSanitize']).
    directive('rbSelect', ['RefBookService', function(RefBookService) {
        return {
            restrict: 'A',
            replace: true,
            scope: {
                id: '=',
                rb: '=',
                ngModel: '='
            },
            link: function ($scope, f, attrs) {
                $scope.rbObj = RefBookService.get(attrs.rb);
            },
            template: '<div><ui-select id=id name="exec_person" theme="select2"' +
                      '    ng-model="ngModel" ng-required="true">' +
                      '<match placeholder="Лечащий врач">[[$select.selected.name]]</match>' +
                      '<choices repeat="item in rbObj.objects | filter: $select.search">' +
                      '    <div ng-bind-html="item.name | highlight: $select.search"></div>' +
                      '</choices>' +
                      '</ui-select></div>'
        };
    }]).
    directive('wmDate', ['$timeout', function ($timeout) {
        return {
            restrict: 'E',
            replace: true,
            scope: {
                id: '@',
                name: '@',
                ngModel: '=',
                ngRequired: '=',
                ngDisabled: '='
            },
            controller: function ($scope) {
                $scope.popup = { opened: false };
                $scope.open_datepicker_popup = function (prev_state) {
                    $timeout(function () {
                        $scope.popup.opened = !prev_state;
                        if (!$scope.ngModel) {
                            $scope.ngModel = new Date();
                        }
                    });
                };
            },
            template: ['<div class="input-group">',
                        '<input type="text" id="[[id]]_inner" name="[[name]]_inner" class="form-control"',
                        'is-open="popup.opened" ng-model="ngModel" autocomplete="off"',
                        'datepicker_popup="dd.MM.yyyy" ng-required="ngRequired" ng-disabled="ngDisabled" manual-date/>',
                        '<span class="input-group-btn">',
                        '<button type="button" class="btn btn-default" ng-click="open_datepicker_popup(popup.opened)" ng-disabled="ngDisabled">',
                        '<i class="glyphicon glyphicon-calendar"></i></button>',
                        '</span>',
                        '</div>'
            ].join('\n')
        };
    }]).
    directive('manualDate', [function() {
        return {
            restrict: 'A',
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift(function(viewValue) {
                    var viewValue = ctrl.$viewValue;
                    if (!viewValue || viewValue instanceof Date) return viewValue;
                    var parts = viewValue.split('.');
                    var d = new Date(parseInt(parts[2]), parseInt(parts[1] - 1),
                        parseInt(parts[0]));
                    if (moment(d).isValid()) {
                        ctrl.$setValidity('date', true);
                        ctrl.$setViewValue(d);
                        return d;
                    } else {
                        ctrl.$setValidity('date', false);
                        return undefined;
                    }
                });
            }
        };
    }])
;
angular.module('WebMis20.validators', [])
.directive('enumValidator', function() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                if (viewValue && viewValue.id > 0) {
                    ctrl.$setValidity('text', true);
                    return viewValue;
                } else {
                    ctrl.$setValidity('text', false);
                    return undefined;
                }
            });
        }
    };
})
.directive('snilsValidator', [function() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            function snilsCRC (value) {
                var v = value.substring(0, 3) + value.substring(4, 7) + value.substring(8, 11) + value.substring(12, 14);
                var result = 0;
                for (var i=0; i < 9; i++) {
                    result += (9 - i) * parseInt(v[i])
                }
                result = (result % 101) % 100;
                if (result < 10) return '0' + result;
                else return '' + result;
            }
            ctrl.$parsers.unshift(function(viewValue) {
                ctrl.$setValidity('text', viewValue && viewValue.substring(12, 14) == snilsCRC(viewValue));
                return viewValue
            });
        }
    };
}])
.directive('validatorRegexp', [function () {
return {
    restrict: 'A',
    require: 'ngModel',
    link: function(scope, elm, attrs, ctrl) {
        var validity_regexp = new RegExp(scope.$eval(attrs.validatorRegexp));
        ctrl.$parsers.unshift(function(viewValue) {
            ctrl.$setValidity('text', viewValue && validity_regexp.test(viewValue));
            return viewValue
        });
        var element = angular.element(elm);
        $compile(element)(scope);
    }
}
}]);
