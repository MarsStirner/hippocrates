'use strict';

angular.module('WebMis20.directives', ['ui.bootstrap', 'ui.select', 'ngSanitize']);

angular.module('WebMis20.directives')
    .directive('rbSelect', ['$compile', '$timeout', function($compile, $timeout) {
        return {
            restrict: 'E',
            require: '^ngModel',
            link: function (scope, element, attrs, ctrl) {
                var _id = attrs.id,
                    name = attrs.name,
                    theme = attrs.theme || "select2",
                    ngDisabled = attrs.ngDisabled,
                    placeholder = attrs.placeholder,
                    ngModel = attrs.ngModel,
                    refBook = attrs.refBook,
                    extra_filter = attrs.extraFilter;
                if (!ngModel) throw new Error('<rb-select> must have ng-model attribute');
                if (!refBook) throw new Error('<rb-select> must have rb attribute');
                var uiSelect = $('<ui-select></ui-select>');
                var uiSelectMatch = $('<ui-select-match>[[ $select.selected.name ]]</ui-select-match>');
                var uiSelectChoices = $(
                    '<ui-select-choices repeat="item in $refBook.objects | {0}filter: $select.search track by item.id">\
                        <div ng-bind-html="item.name | highlight: $select.search"></div>\
                    </ui-select-choices>'
                    .format(extra_filter?(extra_filter + ' | '):'')
                );
                if (_id) uiSelect.attr('id', _id);
                if (name) uiSelect.attr('name', name);
                if (theme) uiSelect.attr('theme', theme);
                if (ngDisabled) uiSelect.attr('ng-disabled', ngDisabled);
                if (ngModel) uiSelect.attr('ng-model', ngModel);
                if (placeholder) uiSelectMatch.attr('placeholder', placeholder);
                if (refBook) uiSelect.attr('ref-book', refBook);
                uiSelect.append(uiSelectMatch);
                uiSelect.append(uiSelectChoices);
                $(element).replaceWith(uiSelect);
                $compile(uiSelect)(scope);
            }
        };
    }])
    .directive('wmDate', ['$timeout', function ($timeout) {
        return {
            restrict: 'E',
            replace: true,
            scope: {
                id: '@',
                ngModel: '=',
                ngRequired: '=',
                ngDisabled: '=',
                maxDate: '='
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
                        '<input type="text" id="[[id]]_inner" name="[[id]]" class="form-control"',
                        'is-open="popup.opened" ng-model="ngModel" autocomplete="off" max="maxDate"',
                        'datepicker_popup="dd.MM.yyyy" ng-required="ngRequired" ng-disabled="ngDisabled"' +
                        'manual-date ui-mask="99.99.9999" date-mask />',
                        '<span class="input-group-btn">',
                        '<button type="button" class="btn btn-default" ng-click="open_datepicker_popup(popup.opened)" ng-disabled="ngDisabled">',
                        '<i class="glyphicon glyphicon-calendar"></i></button>',
                        '</span>',
                        '</div>'
            ].join('\n')
        };
    }])
    .directive('manualDate', [function() {
        return {
            restrict: 'A',
            require: '^ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift(function(_) {
                    var viewValue = ctrl.$viewValue;
                    if (!viewValue || viewValue instanceof Date) {
                        return viewValue;
                    }
                    var d = moment(viewValue.replace('_', ''), "DD.MM.YYYY", true);
                    if (moment(d).isValid()) {
                        ctrl.$setValidity('date', true);
                        ctrl.$setViewValue(d.toDate());
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
                if ($scope.selected_templates.has(template)) {
                    $scope.selected_templates.remove(template);
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
                        if (!$scope.selected_templates.has(template)) {
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
                        else if (['Organisation', 'OrgStructure', 'Person', 'Service'].has(typeName))
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
                        templateUrl: '/WebMis20/modal-print-dialog.html',
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
    .directive('refBook', ['RefBookService', function (RefBookService) {
        return {
            restrict: 'A',
            controller: ['$scope', '$attrs', function ($scope, $attrs) {
                $scope.$refBook = RefBookService.get($attrs.refBook);
            }]
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
                <span class="fs-check-outer"><span ng-show="model" class="fs-check-inner"></span></span>[[ metadata.title ]]</a></div>',
            Date:    '<div fs-date ng-required="true" ng-model="model" class="validatable"></div>',
            Time:    '<div fs-time ng-required="true" ng-model="model" class="validatable"></div>',
            List:    '<div fs-select items="metadata.arguments" ng-model="model" ng-required="true" class="validatable">[[ item ]]</div>',
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
    .service('TocSpy', ['$window', function ($window) {
        var cache = [];
        var toc = null;
        var self = this;
        this.register = function (ctrl, element) {
            cache.push([ctrl, element[0]]);
            var parent = element.parent().controller('tocElement');
            if (parent) {
                parent.$children.push(ctrl);
            }
            element.on('$destroy', function () {
                self.unregister(ctrl);
            });
            $($window).scroll(function () {
                if (!toc) return;
                var i = cache.length;
                var something_changed = false;
                while (i--) {
                    var ctrl = cache[i][0];
                    var elem = cache[i][1];
                    var top = elem.getOffsetRect().top;
                    var height = elem.getBoundingClientRect().height;
                    var shift = $window.pageYOffset - top + 20;
                    var new_active = 0 < shift && shift < height;
                    if (new_active != ctrl.tocIsActive) {
                        ctrl.tocIsActive = new_active;
                        something_changed = true;
                    }
                }
                if (something_changed) {
                    toc.$digest();
                }
            })
        };
        this.unregister = function (ctrl) {
            var i = cache.length;
            while (i--) {
                if (cache[i][0] == ctrl) {
                    cache.splice(i, 1);
                    break;
                }
            }
            if (ctrl.$parent) {
                ctrl.$parent.$children.remove(ctrl)
            }
        };
        this.registerToc = function (the_toc) {
            toc = the_toc;
        }
    }])
    .directive('tocElement', ['TocSpy', function (TocSpy) {
        var merr = angular.$$minErr('tocElement');
        return {
            restrict: 'A',
            require: ['tocElement', '?form'],
            controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
                var self = this;
                if ($scope.hasOwnProperty('$index')) {
                    this.$name = $attrs.name + '_' + $scope.$index;
                } else {
                    this.$name = $attrs.name;
                }
                this.$children = [];
                this.$title = $attrs.tocElement;
                this.$form = null;
                this.$parent = $element.parent().controller('tocElement') || null;
                this.$invalid = function () {
                    if (self.$form) {
                        return self.$form.$invalid;
                    } else {
                        return false;
                    }
                };
                this.tocIsActive = false;
            }],
            link: function (scope, element, attrs, ctrls) {
                if (!attrs.name) {
                    merr('name', 'tocElement directive must have "name" attribute')
                }
                var self_ctrl = ctrls[0],
                    parent_ctrl = element.parent().controller('tocElement');
                self_ctrl.$form = ctrls[1];

                if (parent_ctrl) {
                    TocSpy.register(self_ctrl, element);
                }
                if (attrs.tocName) {
                    scope[attrs.tocName] = self_ctrl;
                }
                var jElement = $(element);
                jElement.attr('id', self_ctrl.$name);
                self_ctrl.element = jElement;
                if (attrs.tocDynamic) {
                    scope.$watch(attrs.tocDynamic, function (new_name) {
                        self_ctrl.$title = new_name;
                    })
                }
            }
        }
    }])
    .directive('tocAffix', ['TocSpy', function (TocSpy) {
        return {
            restrict: 'E',
            scope: {
                tocName: '='
            },
            replace: true,
            transclude: true,
            template:
                '<div class="toc">\
                    <ul class="nav">\
                        <li ng-repeat="node in tocName.$children" ng-class="{\'toc-selected-top\': node.tocIsActive}">\
                            <a ng-href="#[[node.$name]]" class="wrap-btn" ng-class="{\'text-danger bg-danger\': node.$invalid()}">\
                                [[ node.$title ]]\
                            </a>\
                            <ul ng-if="node.$children.length" class="nav">\
                                <li ng-repeat="node in node.$children" ng-class="{\'toc-selected-bottom\': node.tocIsActive}">\
                                    <a ng-href="#[[node.$name]]" class="wrap-btn" ng-class="{\'text-danger bg-danger\': node.$invalid()}">\
                                        [[ node.$title ]]\
                                    </a>\
                                </li>\
                            </ul>\
                        </li>\
                    </ul>\
                    <div ng-transclude></div>\
                </div>',
            link: function (scope, element, attrs) {
                TocSpy.registerToc(scope);
            }
        }
    }])
    .directive('wmOrgStructureTree', ['SelectAll', '$compile', '$http', function (SelectAll, $compile, $http) {
        // depends on wmCustomDropdown
        return {
            restrict: 'E',
            scope: {
                onSelect: '&'
            },
            template:
                '<div class="ui-treeview">\
                    <ul ng-repeat="root in tree.children">\
                        <li sf-treepeat="node in children of root">\
                            <a ng-click="select(node)" ng-if="!node.is_node" class="leaf">\
                                <div class="tree-label leaf">&nbsp;</div>\
                                [[ node.name ]]\
                            </a>\
                            <a ng-if="node.is_node" ng-click="sas.toggle(node.id)" class="node">\
                                <div class="tree-label"\
                                     ng-class="{\'collapsed\': !sas.selected(node.id),\
                                                \'expanded\': sas.selected(node.id)}">&nbsp;</div>\
                                [[ node.name ]]\
                            </a>\
                            <ul ng-if="node.is_node && sas.selected(node.id)">\
                                <li sf-treecurse></li>\
                            </ul>\
                        </li>\
                    </ul>\
                </div>',
            link: function (scope) {
                var scope_query = '';
                var sas = scope.sas = new SelectAll([]);
                var der_tree = new Tree('parent_id');
                var tree = scope.tree = {};

                function doFilter() {
                    var keywords = scope_query.toLowerCase().split();
                    tree = der_tree.filter(function filter(item, idDict) {
                        return !keywords.length || keywords.filter(function (keyword) {
                            return (item.name.toLowerCase()).indexOf(keyword) !== -1
                        }).length == keywords.length
                    });
                    doRender();
                    sas.setSource(tree.masterDict.keys().map(function (key) {
                        var result = parseInt(key);
                        if (isNaN(result)) {
                            return key
                        } else {
                            return result
                        }
                    }));
                    sas.selectAll();
                }

                function doRender() {
                    tree = der_tree.render(make_object);
                    scope.tree.children = tree.root.children;
                }

                function make_object(item, is_node) {
                    if (item === null) {
                        var result = {};
                        result.parent_id = null;
                        result.id = 'root';
                        result.children = [];
                        result.is_node = true;
                        return result
                    }
                    return angular.extend(item, {is_node: is_node});
                }
                $http.get(url_get_orgstructure, {
                    params: {
                        org_id: 3479
                    }
                })
                .success(function (data) {
                    der_tree.set_array(data.result);
                    doFilter();
                });
                scope.$on('FilterChanged', function (event, query) {
                    scope_query = query;
                    doFilter()
                });
                scope.select = function (node) {
                    if (scope.$parent.$ctrl) {
                        scope.$parent.$ctrl.$set_query(node.name);
                        scope.$parent.$ctrl.$select(node);
                    }
                    if (scope.onSelect) {
                        scope.onSelect()(node);
                    }
                }
            }
        }
    }])
    .run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-print-dialog.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="cancel()">&times;</button>\
            <h4 class="modal-title" id="myModalLabel">Печать документов</h4>\
        </div>\
        <table ng-show="page == 0" class="table table-condensed modal-body">\
            <thead>\
                <tr>\
                    <th>\
                        <input type="checkbox" ng-checked="ps.templates.length == selected_templates.length" ng-click="select_all_templates()">\
                        </th>\
                        <th>Наименование</th>\
                    </tr>\
                </thead>\
                <tbody>\
                    <tr ng-repeat="template in ps.templates">\
                        <td>\
                            <input type="checkbox" ng-checked="selected_templates.has(template)" id="template-id-[[template.id]]" ng-click="toggle_select_template(template)">\
                            </td>\
                            <td>\
                                <label for="template-id-[[template.id]]" ng-bind="template.name"></label>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
                <div ng-show="page == 1">\
                    <form name="printing_meta">\
                        <div class="modal-body" ng-repeat="template in selected_templates | filter:template_has_meta">\
                            <p ng-bind="template.name"></p>\
                            <div class="row" ng-repeat="var_meta in template.meta">\
                                <div class="col-md-3">\
                                    <label ng-bind="var_meta.title"></label>\
                                </div>\
                                <div class="col-md-9" ui-print-variable meta="var_meta" model="mega_model[template.id][var_meta.name]">\
                                </div>\
                            </div>\
                        </div>\
                    </form>\
                </div>\
                <div class="modal-footer">\
                    <button type="button" class="btn btn-success" ng-click="btn_next()" ng-if="page == 0 && !instant_print()">\
                    Далее &gt;&gt;</button>\
                    <button type="button" class="btn btn-default" ng-click="btn_prev()" ng-if="page == 1 && !instant_print()">\
                    &lt;&lt; Назад</button>\
                    <button type="button" class="btn btn-primary" ng-click="print_separated()" ng-if="page == 1 || instant_print()"\
                    ng-disabled="printing_meta.$invalid">Печать</button>\
                    <button type="button" class="btn btn-primary" ng-click="print_compact()" ng-if="page == 1 || instant_print()"\
                    ng-disabled="printing_meta.$invalid">Печать компактно</button>\
                    <button type="button" class="btn btn-default" ng-click="cancel()">Отмена</button>\
                </div>')
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
                ctrl.$setValidity('text', viewValue == "" || viewValue && viewValue.substring(12, 14) == snilsCRC(viewValue));
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
}])
.directive('formSafeClose', ['$timeout', function ($timeout) {
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
            // Чтобы обойти баг FF с повторным вызовом onbeforeunload (http://stackoverflow.com/a/2295156/1748202)
            $scope.onBeforeUnloadFired = false;

            $scope.ResetOnBeforeUnloadFired = function () {
               $scope.onBeforeUnloadFired = false;
            };
            window.onbeforeunload = function(evt){
                if (form.$dirty && !$scope.onBeforeUnloadFired) {
                    $scope.onBeforeUnloadFired = true;
                    if (typeof evt == "undefined") {
                        evt = window.event;
                    }
                    if (evt) {
                        evt.returnValue = message;
                    }
                    $timeout($scope.ResetOnBeforeUnloadFired);
                    return message;
                }
            };
        }
    }
}])
.directive('validNumber', function() {
  return {
    require: '?ngModel',
    link: function(scope, element, attrs, ngModelCtrl) {
      if(!ngModelCtrl) {
        return;
      }
      var allowFloat = attrs.hasOwnProperty('validNumberFloat');
      var allowNegative = attrs.hasOwnProperty('validNumberNegative');
      var regex = new RegExp('[^0-9' + (allowFloat?'\\.':'') + (allowNegative?'-':'') + ']+', 'g');

      var min_val,
          max_val;
      scope.$watch(function () {
          return parseInt(scope.$eval(attrs.minVal));
      }, function (n, o) {
          min_val = n;
      });
      scope.$watch(function () {
          return parseInt(scope.$eval(attrs.maxVal));
      }, function (n, o) {
          max_val = n;
      });

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
          if (angular.isNumber(val)) {
              return val;
          }
        var clean = clear_char_duplicates(val.replace(regex, ''), '.');
        clean = clean !== '' ? parseFloat(clean) : min_val;
        if (!isNaN(min_val)) {
            clean = Math.min(Math.max(clean, min_val), max_val);
        }
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
          var value = parseFloat(this.value);
          if (isNaN(value)) {
              this.value = null;
          } else {
              this.value = value;
          }
      });
    }
  };
});
