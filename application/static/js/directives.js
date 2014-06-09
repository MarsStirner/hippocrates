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
    .directive('uiAlertList', ['$compile', function ($compile) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var e = $(element);
                e.addClass('marginal');
                var subelement = $(
                    '<alert ng-repeat="alert in ' + attrs.uiAlertList + '" type="alert.type" close="alerts.splice(index, 1)">\
                        <span ng-bind="alert.text"></span> [<span ng-bind="alert.code"></span>]\
                    </alert>'
                );
                e.prepend(subelement);
                $compile(subelement)(scope);
            }
        }
    }])
    .directive('uiPrintButton', ['$modal', function ($modal) {
        var ModalPrintDialogController = function ($scope, $modalInstance, ps, context_extender) {
            $scope.aux = aux;
            $scope.page = 0;
            $scope.ps = ps;
            $scope.selected_templates = [];
            $scope.mega_model = {};
            $scope.toggle_select_template = function (template) {
                if (aux.inArray($scope.selected_templates, template)) {
                    $scope.selected_templates.splice($scope.selected_templates.indexOf(template), 1);
                    $scope.mega_model[template.id] = undefined;
                } else {
                    $scope.selected_templates.push(template);
                    make_model(template);
                }
                $scope.selected_templates.sort(function (left, right) {
                    return (left.code < right.code) ? -1 : (left.code > right.code ? 1 : 0)
                });
            };
            $scope.select_all_templates = function () {
                if ($scope.selected_templates.length == ps.templates.length) {
                    $scope.selected_templates = [];
                    $scope.mega_model = {};
                } else {
                    $scope.selected_templates = ps.templates.map(function (template) {
                        if (! aux.inArray($scope.selected_templates, template)) {
                            make_model(template)
                        }
                        return template;
                    })
                }
            };
            $scope.btn_next = function () {
                $scope.page = 1;
            };
            $scope.btn_prev = function () {
                $scope.mega_model = {};
                $scope.page = 0;
            };
            function prepare_data () {
                return $scope.selected_templates.map(function (template) {
                    return {
                        template_id: template.id,
                        context: angular.extend({}, $scope.mega_model[template.id], context_extender)
                    }
                })
            }
            function make_model (template) {
                if (template.meta) {
                    var desc = $scope.mega_model[template.id] = {};
                    template.meta.map(function (variable) {
                        desc[variable.name] = null;
                    })
                }
            }
            $scope.print_separated = function () {
                ps.print_template(prepare_data(), true)
            };
            $scope.print_compact = function () {
                ps.print_template(prepare_data(), false)
            };
            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
            $scope.instant_print = function () {
                return ! $scope.selected_templates.filter(function (template) {
                    return Boolean(template.meta.length)
                }).length;
            };
            $scope.can_print = function () {
                return $scope.selected_templates.length > 0;
            };
            $scope.template_has_meta = function (template) {
                return Boolean(template.meta.length);
            };
            $scope.select_all_templates();
        };
        return {
            restrict: 'E',
            replace: true,
            template:
                /* '<div class="dropup"">\
                    <button class="btn btn-lg btn-default dropdown-toggle" type="button" id="print_dropdownMenu"\
                            data-toggle="dropdown" ng-disabled="!$ps.templates">\
                        <span class="glyphicon glyphicon-print"></span> Печать <span class="caret"></span>\
                    </button>\
                    <ul class="dropdown-menu dropdown-menu" role="menu" aria-labelledby="print_dropdownMenu">\
                        <li role="presentation" ng-repeat="template in $ps.templates">\
                            <a role="menuitem" tabindex="-1" href="" class="print_template"\
                               ng-click="$ps.print_template(template.id)" ng-bind="template.name"></a>\
                        </li>\
                    </ul>\
                </div>',*/
                '<button class="btn" ng-click="open_print_window()">Печать</button>',
            scope: {
                $ps: '=ps'
            },
            link: function (scope, element, attrs) {
                var resolver_call = attrs.resolve;
                scope.open_print_window = function () {
                    var modal = $modal.open({
                        templateUrl: 'modal-print-dialog.html',
                        controller: ModalPrintDialogController,
                        resolve: {
                            ps: function () {
                                return scope.$ps;
                            },
                            context_extender: function () {
                                return scope.$parent.$eval(resolver_call)
                            }
                        }
                    })
                }
            }
        }
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
.directive('snilsValidator', ['$timeout', function ($timeout) {
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
                $timeout(function(){
                    if (ctrl.$invalid){
                        elm.trigger('show_popover');
                    } else {
                        elm.trigger('hide_popover');
                    }
                });
                return viewValue;
            });
        }
    };
}])
.directive('validatorRegexp', [function () {
return {
    restrict: 'A',
    require: 'ngModel',
    link: function(scope, element, attrs, ctrl) {
        var regexp = null;
        var evalue = null;
        scope.$watch(attrs.validatorRegexp, function (n, o) {
            evalue = n;
            if (!evalue) {
                ctrl.$setViewValue('');
                ctrl.$render();
                ctrl.$setValidity('text', true);
                $(element).attr('disabled', true);
            } else {
                $(element).removeAttr('disabled');
                regexp = new RegExp(evalue);
                ctrl.$setValidity('text', ctrl.$viewValue && regexp.test(ctrl.$viewValue));
            }
        });
        ctrl.$parsers.unshift(function(viewValue) {
            if (evalue && regexp) {
                ctrl.$setValidity('text', viewValue && regexp.test(viewValue));
            }
            return viewValue
        });
    }
}
}]);
