'use strict';

angular.module('WebMis20.directives', ['ui.bootstrap', 'ui.select', 'ngSanitize']);

angular.module('WebMis20.directives').
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
                      '<ui-select-match placeholder="Лечащий врач">[[$select.selected.name]]</ui-select-match>' +
                      '<ui-select-choices repeat="item in rbObj.objects | filter: $select.search">' +
                      '    <div ng-bind-html="item.name | highlight: $select.search"></div>' +
                      '</ui-select-choices>' +
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
                    var context = {};
                    template.meta.map(function (meta) {
                        var name = meta.name;
                        var typeName = meta['type'];
                        var value = $scope.mega_model[template.id][name];
                        if (typeName == 'Integer')
                            context[name] = parseInt(value);
                        else if (typeName == 'Float')
                            context[name] = parseFloat(value);
                        else if (typeName == 'Boolean')
                            context[name] = Boolean(value);
                        else if (aux.inArray(['Organisation', 'OrgStructure', 'Person', 'Service'], typeName))
                            context[name] = value ? value.id : null;
                        else context[name] = value
                    });
                    return {
                        template_id: template.id,
                        context: angular.extend(context, context_extender)
                    }
                })
            }
            function make_model (template) {
                if (template.meta) {
                    var desc = $scope.mega_model[template.id] = {};
                    template.meta.map(function (variable) {
                        desc[variable.name] = variable.default;
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
            template: '<button class="btn btn-default" ng-click="open_print_window()" title="Печать"><i class="glyphicon glyphicon-print"></i></button>',
            scope: {
                $ps: '=ps'
            },
            link: function (scope, element, attrs) {
                var resolver_call = attrs.resolve;
                scope.open_print_window = function () {
                    var modal = $modal.open({
                        templateUrl: 'modal-print-dialog.html',
                        controller: ModalPrintDialogController,
                        size: 'lg',
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
    .directive('refBookSelect', ['RefBookService', function (RefBookService) {
        return {
            restrict: 'E',
            replace: true,
            template:
                '<ui-select ng-model="model" theme="select2">\
                    <choices repeat="rt in $refBook.objects |filter: $select:search | limit: 100">\
                        <div ng-bind-html="rt.name | highlight: $select.search"></div>\
                    </chioces>\
                </ui-select>',
            link: function (scope, element, attributes) {
                scope.$refBook = RefBookService.get(attributes.refBook);
                scope.model = attributes.model;
            }
        }
    }])
    .directive('uiPrintVariable', ['$compile', 'RefBookService', function ($compile, RefBookService) {
        var ui_select_template =
            '<div fs-select="" items="$refBook.objects" ng-required="true" ng-model="model" class="validatable">[[item.name]]</div>';
        var templates = {
            Integer: '<input ng-required="true" class="validatable form-control" type="text" ng-pattern="/^([1-9]\\d*|0)$/" ng-model="model"></input>',
            String:  '<input ng-required="true" class="validatable form-control" type="text" ng-model="model"></input>',
            Float:   '<input ng-required="true" class="validatable form-control" type="text" ng-pattern="/^([1-9]\\d*|0)(.\\d+)?$/" ng-model="model"></input>',
            Boolean:
                '<div class="fs-checkbox fs-racheck">\
                    <a class="fs-racheck-item" href="javascript:void(0)" ng-click="model = !model" fs-space="model = !model">\
                <span class="fs-check-outer"><span ng-show="model" class="fs-check-inner"></span></span>[[ metadata.title ]]</a></input>',
            Date:    '<div fs-date ng-required="true" ng-model="model" class="validatable"></div>',
            Time:    '<div fs-time ng-required="true" ng-model="model" class="validatable"></div>',
            List:    '<div fs-select items="metadata.arguments" ng-model="model" ng-required="true" class="validatable">[[ item ]]</select>',
            Multilist: '<div fs-checkbox items="metadata.arguments" ng-model="model" class="validatable">[[ item ]]</div>',
            RefBook: ui_select_template,
            Organisation:
                '<div fs-select="" items="$refBook.objects" ng-required="true" ng-model="model" class="validatable">[[item.short_name]]</div>',
            OrgStructure: ui_select_template,
            Person:  ui_select_template,
            Service: ui_select_template,
            SpecialVariable: 'Special Variable'
        };
        return {
            restrict: 'A',
            scope: {
                metadata: '=meta',
                model: '=model'
            },
            link: function (scope, element, attributes) {
                var typeName = scope.metadata['type'];
                if (typeName == "RefBook") scope.$refBook = RefBookService.get(scope.metadata['arguments'][0]);
                if (typeName == "Organisation") scope.$refBook = RefBookService.get('Organisation');
                if (typeName == "OrgStructure") scope.$refBook = RefBookService.get('OrgStructure');
                if (typeName == "Person") scope.$refBook = RefBookService.get('Person');
                if (typeName == "Service") scope.$refBook = RefBookService.get('rbService');
                var template = templates[typeName];
                var child = $(template);
                $(element).append(child);
                $compile(child)(scope);
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
                if (ctrl.$viewValue) {
                    ctrl.$setViewValue('');
                    ctrl.$render();
                };
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
}]).directive('formSafeClose', [function () {
return {
    restrict: 'A',
    require: 'form',
    link: function($scope, element, attrs, form) {
        var message = "Вы уверены, что хотите закрыть вкладку? Форма может содержать несохранённые данные.";
        $scope.$on('$locationChangeStart', function(event, next, current) {
            if (form.$dirty) {
                if(!confirm(message)) {
                    event.preventDefault();
                }
            }
        });

        window.onbeforeunload = function(evt){
            if (form.$dirty) {
                if (typeof evt == "undefined") {
                    evt = window.event;
                }
                if (evt) {
                    evt.returnValue = message;
                }
                return message;
            }
        };
    }
}
}]).directive('validNumber', function() {
  return {
    require: '?ngModel',
    link: function(scope, element, attrs, ngModelCtrl) {
      if(!ngModelCtrl) {
        return;
      }
      function clear_char_duplicates(string, char){
        var arr = string.split(char);
        var res;
        if (arr.length > 1){
            res = arr.shift();
            res += char + arr.shift();
            res += arr.join('');
        }else{
            res = arr[0];
        }
          return res;
      }
      ngModelCtrl.$parsers.push(function(val) {
//        var clean = val.replace( /[^0-9\.\-]+/g, ''); Если вдруг захотим отрицательные
        var clean = val.replace( /[^0-9\.]+/g, '');
        clean = clear_char_duplicates(clean, '.');
        if (val !== clean) {
          ngModelCtrl.$setViewValue(clean);
          ngModelCtrl.$render();
        }
        return clean;
      });

      element.bind('keypress', function(event) {
        if(event.keyCode === 32) {
          event.preventDefault();
        }
      });

      element.bind('blur', function(event) {
          this.value = parseFloat(this.value);
      });
    }
  };
});
