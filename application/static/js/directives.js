'use strict';

angular.module('WebMis20.directives', ['ui.bootstrap', 'ui.select', 'ngSanitize', 'WebMis20.directives.goodies']);

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
    .directive('wmPersonSelect', ['$compile', function ($compile) {
        return {
            restrict: 'E',
            require: 'ngModel',
            link: function (scope, element, attrs) {
                var template = '\
    <ui-select {0} {1} theme="select2" class="form-control" autocomplete="off" ref-book="vrbPersonWithSpeciality" ng-model="{2}" {3}>\
        <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]][[$select.selected.name ? ", ": null]][[ $select.selected.speciality.name ]]</ui-select-match>\
        <ui-select-choices repeat="item in $refBook.objects | filter: $select.search | limitTo: 50">\
            <span ng-bind-html="(item.name + \', \' + item.speciality.name) | highlight: $select.search"></span>\
        </ui-select-choices>\
    </ui-select>'.format(
                    attrs.id ? 'id="{0}"'.format(attrs.id) : '',
                    attrs.name ? 'name="{0}"'.format(attrs.name) : '',
                    attrs.ngModel,
                    attrs.ngDisabled ? 'ng-disabled="{0}"'.format(attrs.ngDisabled) : ''
                );
                var elm = $compile(template)(scope);
                element.replaceWith(elm);
            }
        }
    }])
    .directive('bakLabView', [function () {
        return {
            restrict: 'E',
            scope: {
                bak_model: '=model'
            },
            link: function (scope, elm, attrs) {
                scope.get_row_num = function (organism) {
                    return organism.sens_values.length || 1;
                };
            },
            template:
    '<legend class="vmargin10">Результаты БАК исследования</legend>\
     <div class="row">\
        <div class="col-md-6">\
            <label>Подписавший врач:&nbsp;</label>\
            <span>[[bak_model.doctor ? \'{0}, {1}\'.format(bak_model.doctor.name, bak_model.doctor.speciality.name) : \'\']]</span>\
        </div>\
        <div class="col-md-6">\
            <label>Код Лис:&nbsp;</label><span>[[bak_model.code_lis]]</span>\
        </div>\
     </div>\
     <div class="row">\
        <div class="col-md-6">\
            <label>Завершено:&nbsp;</label><span>[[bak_model.final ? "Да" : "Нет"]]</span>\
        </div>\
        <div class="col-md-6">\
            <label>Дефекты БМ:&nbsp;</label><span>[[bak_model.defects]]</span>\
        </div>\
     </div>\
     <table class="table table-condensed table-bordered table-bak">\
        <thead ng-if="bak_model.organisms.length">\
            <tr>\
                <th rowspan="2">Микроорганизм</th>\
                <th rowspan="2">Концентрация</th>\
                <th colspan="3">Чувствительность к антибиотикам</th>\
            </tr>\
            <tr>\
                <th>Антибиотик</th>\
                <th>Концентрация</th>\
                <th>Чувствительность</th>\
            </tr>\
        </thead>\
        <tbody ng-repeat="organism in bak_model.organisms" ng-class="{\'bg-muted\': hover}" ng-mouseenter="hover=true" ng-mouseleave="hover=false">\
            <tr>\
                <td rowspan="[[get_row_num(organism)]]">[[organism.microorganism]]</td>\
                <td rowspan="[[get_row_num(organism)]]">[[organism.concentration]]</td>\
                <td>[[organism.sens_values[0].antibiotic]]</td>\
                <td>[[organism.sens_values[0].mic]]</td>\
                <td>[[organism.sens_values[0].activity]]</td>\
            </tr>\
            <tr ng-repeat="sens in organism.sens_values.slice(1)">\
                <td>[[sens.antibiotic]]</td>\
                <td>[[sens.mic]]</td>\
                <td>[[sens.activity]]</td>\
            </tr>\
        </tbody>\
        <tbody ng-if="bak_model.comments.length">\
            <tr>\
                <th colspan="5">Комментарии</th>\
            </tr>\
            <tr ng-repeat="comment in bak_model.comments" ng-class="{\'bg-muted\': hover}" ng-mouseenter="hover=true" ng-mouseleave="hover=false">\
                <td colspan="5">[[comment.text]]</td>\
            </tr>\
        </tbody>\
     </table>'
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
                        <span ng-if="alert.data.detailed_msg">\
                            <a href="javascript:void(0);"  ng-click="show_details = !show_details">\
                                [[show_details ? "[Скрыть]" : "[Подробнее]"]]\
                            </a>\
                            <span ng-show="show_details">[[alert.data.detailed_msg]]: [[alert.data.err_msg]]</span>\
                        </span>\
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
                        else if (typeName == 'SpecialVariable') {
                            if (!('special_variables' in context))
                                context['special_variables']={};
                            context['special_variables'][name] = meta['arguments'];
                        }

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
                ps.print_template(prepare_data(), true).then(
                    function () {
                        angular.noop();
                    },
                    function () {
                        $scope.$close();
                    }
                );
            };
            $scope.print_compact = function () {
                ps.print_template(prepare_data(), false).then(
                    function () {
                        angular.noop();
                    },
                    function () {
                        $scope.$close();
                    }
                );
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
                '<button class="btn btn-default" ng-click="print_templates()" title="Печать" ng-disabled="disabled()">\
                    <i class="glyphicon glyphicon-print"></i>\
                    <i class="glyphicon glyphicon-remove text-danger" ng-show="disabled()"></i>\
                 </button>',
            scope: {
                $ps: '=ps',
                beforePrint: '&?'
            },
            link: function (scope, element, attrs) {
                var resolver_call = attrs.resolve;
                if (!attrs.beforePrint) {scope.beforePrint=null};
                scope.disabled = function () {
                    return !scope.$ps.is_available();
                };
                scope.print_templates = function(){
                    if (scope.beforePrint){
                        scope.beforePrint().then(scope.open_print_window());
                    } else {
                        scope.open_print_window();
                    }

                }
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
            link: function (scope, elem, attrs) {
                var isolatedScope = elem.isolateScope();
                if (isolatedScope){
                    isolatedScope.$refBook = RefBookService.get(attrs.refBook);
                } else {
                scope.$refBook = RefBookService.get(attrs.refBook);
                }
            }
        }
    }])
    .directive("refbookCheckbox", [
        '$window', function($window) {
          return {
            restrict: "A",
            scope: {
              disabled: '=ngDisabled',
              required: '=',
              errors: '=',
              inline: '='
            },
            require: '?ngModel',
            replace: true,
            template: function(el, attrs) {
              var itemTpl, template;
              itemTpl = el.html() || 'template me: {{item | json}}';
              return template = "<div class='fs-racheck fs-checkbox' ng-class=\"{disabled: disabled, enabled: !disabled}\">\n  <div ng-repeat='item in $refBook.objects'>\n    <a class=\"fs-racheck-item\"\n       href='javascript:void(0)'\n       ng-disabled=\"disabled\"\n       ng-click=\"toggle(item)\"\n       fs-space='toggle(item)'>\n      <span class=\"fs-check-outer\"><span ng-show=\"isSelected(item)\" class=\"fs-check-inner\"></span></span>\n      " + itemTpl + "\n    </a>\n  </div>\n</div>";
            },
            controller: function($scope, $element, $attrs) {
              $scope.toggle = function(item) {
                if ($scope.disabled) {
                  return;
                }
                if (!$scope.isSelected(item)) {
                  $scope.selectedItems.push(item);
                } else {
                  $scope.selectedItems.splice(indexOf($scope.selectedItems, item), 1);
                }
                return false;
              };
              $scope.isSelected = function(item) {
                return indexOf($scope.selectedItems, item) > -1;
              };
              $scope.invalid = function() {
                return ($scope.errors != null) && $scope.errors.length > 0;
              };
              return $scope.selectedItems = [];
            },
            link: function(scope, element, attrs, ngModelCtrl, transcludeFn) {
              var setViewValue;
              if (ngModelCtrl) {
                setViewValue = function(newValue, oldValue) {
                  if (!angular.equals(newValue, oldValue)) {
                    return ngModelCtrl.$setViewValue(scope.selectedItems);
                  }
                };
                scope.$watch('selectedItems', setViewValue, true);
                return ngModelCtrl.$render = function() {
                  if (!scope.disabled) {
                    return scope.selectedItems = ngModelCtrl.$viewValue || [];
                  }
                };
              }
            }
          };
        }
      ])
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
    .directive('wmOrgStructureTree', ['SelectAll', '$compile', '$http', 'FlatTree', function (SelectAll, $compile, $http, FlatTree) {
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
                var der_tree = new FlatTree('parent_id');
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
    .directive('wmDiagnosis', ['DiagnosisModal', 'WMEventServices', function(DiagnosisModal, WMEventServices){
        return{
            restrict: 'E',
            require: '^ngModel',
            replace: true,
            scope: {
                ngModel: '=',
                addNew: '=',
                clickable: '='
            },
            controller: function ($scope) {
                $scope.add_new_diagnosis = function () {
                    var new_diagnosis = WMEventServices.add_new_diagnosis();
                    DiagnosisModal.openDiagnosisModal(new_diagnosis).then(function () {
                        $scope.ngModel.push(new_diagnosis);
                    });
                };
                $scope.delete_diagnosis = function (diagnosis) {
                    WMEventServices.delete_diagnosis($scope.ngModel, diagnosis);
                };
                $scope.edit_diagnosis = function (diagnosis) {
                    DiagnosisModal.openDiagnosisModal(diagnosis);
                };
                $scope.open_action = function (action_id) {
                    if(action_id && $scope.clickable){
                        window.open(url_for_schedule_html_action + '?action_id=' + action_id);
                    }
                };
            },
            template: '<div class="row">\
                            <div class="col-md-12">\
                                <table class="table table-condensed">\
                                    <thead>\
                                        <tr>\
                                            <th>Дата начала</th>\
                                            <th>Тип</th>\
                                            <th>Характер</th>\
                                            <th>Код МКБ</th>\
                                            <th>Врач</th>\
                                            <th>Примечание</th>\
                                            <th></th>\
                                            <th></th>\
                                        </tr>\
                                    </thead>\
                                    <tbody>\
                                        <tr class="[[clickable && diag.action_id ? \'row-clickable\' : \'\']]" ng-repeat="diag in ngModel | flt_not_deleted">\
                                            <td  ng-click="open_action(diag.action_id)">[[diag.set_date | asDate]]</td>\
                                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis_type.name]]</td>\
                                            <td ng-click="open_action(diag.action_id)">[[diag.character.name]]</td>\
                                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis.mkb.code]] [[diag.diagnosis.mkb.name]]</td>\
                                            <td ng-click="open_action(diag.action_id)">[[diag.person.name]]</td>\
                                            <td ng-click="open_action(diag.action_id)">[[diag.notes]]</td>\
                                            <td>\
                                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать"\
                                                        ng-click="edit_diagnosis(diag)"><span class="glyphicon glyphicon-pencil"></span>\
                                                </button>\
                                            </td>\
                                            <td>\
                                                <button type="button" class="btn btn-sm btn-danger" title="Удалить"\
                                                        ng-click="delete_diagnosis(diag)"><span class="glyphicon glyphicon-trash"></span>\
                                                </button>\
                                            </td>\
                                        </tr>\
                                        <tr ng-if="addNew">\
                                            <td colspan="6">\
                                                <button type="button" class="btn btn-sm btn-primary" title="Добавить"\
                                                        ng-click="add_new_diagnosis()">Добавить\
                                                </button>\
                                            </td>\
                                        </tr>\
                                    </tbody>\
                                </table>\
                            </div>\
                        </div>',
            link: function(scope, elm, attrs, ctrl){

            }
        }
    }])
.service('DiagnosisModal', ['$modal', 'WMEvent', function ($modal, WMEvent) {
    return {
        openDiagnosisModal: function (model) {
            var locModel = angular.copy(model);
            var Controller = function ($scope, $modalInstance) {
                $scope.model = locModel;
                $scope.filter_type = function() {
                    return function(elem) {
                        return ["1", "2", "3", "7", "9", "11"].indexOf(elem.code) > -1;
                    };
                };
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-edit-diagnosis.html',
                size: 'lg',
                controller: Controller
            });
            return instance.result.then(function() {
                angular.extend(model, locModel);
            });
        }
    }
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-edit-diagnosis.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">Диагноз</h4>\
        </div>\
        <div class="modal-body">\
            <ng-form name="DiagnosisForm">\
                <div class="row marginal">\
                    <div class="col-md-4">\
                        <div class="form-group"\
                             ng-class="{\'has-error\': DiagnosisForm.diagnosis_type.$invalid}">\
                            <label for="diagnosis_type" class="control-label">Тип</label>\
                            <ui-select class="form-control" name="diagnosis_type" theme="select2"\
                                ng-model="model.diagnosis_type"\
                                ref-book="rbDiagnosisType"\
                                ng-required="true">\
                                <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                                <ui-select-choices repeat="dt in ($refBook.objects | filter: $select.search | filter: filter_type()) track by dt.id">\
                                    <span ng-bind-html="dt.name | highlight: $select.search"></span>\
                                </ui-select-choices>\
                            </ui-select>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <div class="form-group" ng-class="{\'has-error\': DiagnosisForm.set_date.$invalid}">\
                            <label for="diagnosis_date" class="control-label">Дата начала</label>\
                            <wm-date name="set_date" ng-model="model.set_date" ng-required="true">\
                            </wm-date>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <div class="form-group" ng-class="{\'has-error\': DiagnosisForm.end_date.$invalid}">\
                            <label for="diagnosis_date" class="control-label">Дата окончания</label>\
                            <wm-date name="end_date" ng-model="model.end_date">\
                            </wm-date>\
                        </div>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-3">\
                        <div class="form-group"\
                        ng-class="{\'has-error\': DiagnosisForm.mkb.$invalid}">\
                            <label for="MKB" class="control-label">МКБ</label>\
                            <ui-mkb ng-model="model.diagnosis.mkb" name="mkb" ng-required="true"></ui-mkb>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="diagnosis_character" class="control-label">Характер</label>\
                        <ui-select class="form-control" name="diagnosis_character" theme="select2"\
                            ng-model="model.character"\
                            ref-book="rbDiseaseCharacter">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ct in ($refBook.objects | filter: $select.search) track by ct.id">\
                                <span ng-bind-html="ct.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-4">\
                        <div class="form-group"\
                        ng-class="{\'has-error\': model.person == null}">\
                            <label for="diagnosis_person" class="control-label">Врач</label>\
                            <wm-person-select ng-model="model.person" name="diagnosis_person" ng-required="true"></wm-person-select>\
                        </div>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-4">\
                        <label for="result" class="control-label">Результат</label>\
                        <ui-select class="form-control" name="result" theme="select2"\
                            ng-model="model.result"\
                            ref-book="rbResult">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="r in ($refBook.objects | filter: $select.search | rb_result_filter: 2) track by r.id">\
                                <span ng-bind-html="r.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-4">\
                        <label for="ache_result" class="control-label">Исход</label>\
                        <ui-select class="form-control" name="ache_result" theme="select2"\
                            ng-model="model.ache_result"\
                            ref-book="rbAcheResult">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ar in ($refBook.objects | filter: $select.search) track by ar.id">\
                                <span ng-bind-html="ar.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-9">\
                        <label for="diagnosis_description" class="control-label">Описание диагноза</label>\
                        <wysiwyg ng-model="model.diagnosis_description"/>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-12">\
                        <button class="btn btn-default btn-sm" ng-click="expanded=!expanded">\
                            <span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span>\
                        </button>\
                    </div>\
                </div>\
                <div class="row marginal" ng-if="expanded">\
                    <div class="col-md-3">\
                        <label for="phase" class="control-label">Фаза</label>\
                        <ui-select class="form-control" name="phase" theme="select2"\
                            ng-model="model.phase"\
                            ref-book="rbDiseasePhases">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="dp in ($refBook.objects | filter: $select.search) track by dp.id">\
                                <span ng-bind-html="dp.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="stage" class="control-label">Стадия</label>\
                        <ui-select class="form-control" name="stage" theme="select2"\
                            ng-model="model.stage"\
                            ref-book="rbDiseaseStage">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ds in ($refBook.objects | filter: $select.search) track by ds.id">\
                                <span ng-bind-html="ds.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal" ng-if="expanded">\
                    <div class="col-md-3">\
                        <label for="trauma" class="control-label">Травма</label>\
                        <ui-select class="form-control" name="trauma" theme="select2"\
                            ng-model="model.trauma_type"\
                            ref-book="rbTraumaType">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="tt in ($refBook.objects | filter: $select.search) track by tt.id">\
                                <span ng-bind-html="tt.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="health_group" class="control-label">Группа здоровья</label>\
                        <ui-select class="form-control" name="health_group" theme="select2"\
                            ng-model="model.health_group"\
                            ref-book="rbHealthGroup">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="hg in ($refBook.objects | filter: $select.search) track by hg.id">\
                                <span ng-bind-html="hg.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="dispanser" class="control-label">Диспансерное наблюдение</label>\
                        <ui-select class="form-control" name="dispanser" theme="select2"\
                            ng-model="model.dispanser"\
                            ref-book="rbDispanser">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="d in ($refBook.objects | filter: $select.search) track by d.id">\
                                <span ng-bind-html="d.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal" ng-if="expanded">\
                    <div class="col-md-6">\
                    <label for="notes" class="control-label">Примечание</label>\
                    <textarea class="form-control" id="notes" name="notes" rows="2" autocomplete="off" ng-model="model.notes"></textarea>\
                    </div>\
                </div>\
            </ng-form>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            <button type="button" class="btn btn-success" ng-click="$close()"\
            ng-disabled="DiagnosisForm.$invalid">Сохранить</button>\
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
                    if ($(element).attr('ui-mask')){viewValue = viewValue.replace(/_$/, '')};
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
        link: function (scope, element, attrs, ngModelCtrl) {
            if (!ngModelCtrl) {
                return;
            }
            var allowFloat = attrs.hasOwnProperty('validNumberFloat');
            var allowNegative = attrs.hasOwnProperty('validNumberNegative');
            var regex = new RegExp('[^0-9' + (allowFloat ? '.' : '') + (allowNegative ? '-' : '') + ']+', 'g');

            var min_val,
                max_val,
                precision = 0;
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

            function clear_char_duplicates(string, char) {
                var arr = string.split(char);
                var res;
                if (arr.length > 1) {
                    res = arr.shift();
                    res += char + arr.shift();
                    res += arr.join('');
                } else {
                    res = arr[0];
                }
                return res;
            }

            function format_view_value(val, clean_val) {
                if (allowFloat) {
                    return (val.endswith('.') &&  val.indexOf('.') === val.length - 1) ?
                        (clean_val + '.') :
                        clean_val.toFixed(precision);
                } else {
                    return clean_val;
                }
            }

            function calc_precision(val) {
                if (allowFloat){
                    var precision = val.length -
                        (val.indexOf('.') !== -1 ? val.indexOf('.') : val.length) -
                        (val.endswith('.') ? 0 : 1);
                    precision = Math.min(Math.max(precision, 0), 20);
                    return precision;
                } else {
                    return 0;
                }
            }

            ngModelCtrl.$parsers.push(function (val) {
                if (angular.isNumber(val)) {
                    return val;
                }
                var clean = clear_char_duplicates(val.replace(regex, ''), '.');
                precision = calc_precision(clean);
                clean = clean !== '' ? parseFloat(clean) : min_val;
                if (!isNaN(min_val)) {
                    clean = Math.max(clean, min_val);
                }
                if (!isNaN(max_val)) {
                    clean = Math.min(clean, max_val);
                }
                if (val !== clean) {
                    ngModelCtrl.$viewValue = format_view_value(val, clean);
                    ngModelCtrl.$render();
                }
                return clean;
            });

            element.bind('keypress', function (event) {
                if (event.keyCode === 32) {
                    event.preventDefault();
                }
            });

            element.bind('blur', function (event) {
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
