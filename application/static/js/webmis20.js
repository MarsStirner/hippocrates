/**
 * Created by mmalkov on 10.02.14.
 */
var WebMis20 = angular.module('WebMis20', [
    'WebMis20.services',
    'WebMis20.directives',
    'WebMis20.controllers',
    'WebMis20.LoadingIndicator',
    'WebMis20.validators',
    'ui.bootstrap',
    'ui.select',
    'ngSanitize',
    'ngCkeditor',
    'sf.treeRepeat',
    'ui.mask',
    'formstamp',
    'mgcrea.ngStrap.affix'
])
.config(function ($interpolateProvider, datepickerConfig, datepickerPopupConfig) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
    datepickerConfig.showWeek = false;
    datepickerConfig.startingDay = 1;
    datepickerPopupConfig.currentText = 'Сегодня';
    datepickerPopupConfig.toggleWeeksText = 'Недели';
    datepickerPopupConfig.clearText = 'Убрать';
    datepickerPopupConfig.closeText = 'Готово';
//    datepickerPopupConfig.appendToBody=true;
}).config(['$tooltipProvider', function($tooltipProvider){
    $tooltipProvider.setTriggers({
        'mouseenter': 'mouseleave',
        'click': 'click',
        'focus': 'blur',
        'never': 'mouseleave',
        'show_popover': 'hide_popover'
    })
}])
// Workaround for bug #1404
// https://github.com/angular/angular.js/issues/1404
// Source: http://plnkr.co/edit/hSMzWC?p=preview
    .config(['$provide', function($provide) {
    $provide.decorator('ngModelDirective', ['$delegate', function($delegate) {
        var ngModel = $delegate[0], controller = ngModel.controller;
        ngModel.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
            var $interpolate = $injector.get('$interpolate');
            attrs.$set('name', $interpolate(attrs.name || '')(scope));
            $injector.invoke(controller, this, {
                '$scope': scope,
                '$element': element,
                '$attrs': attrs
            });
        }];
        return $delegate;
    }]);
    $provide.decorator('formDirective', ['$delegate', function($delegate) {
        var form = $delegate[0], controller = form.controller;
        form.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
            var $interpolate = $injector.get('$interpolate');
            attrs.$set('name', $interpolate(attrs.name || attrs.ngForm || '')(scope));
            $injector.invoke(controller, this, {
                '$scope': scope,
                '$element': element,
                '$attrs': attrs
            });
        }];
        return $delegate;
    }]);
}])
.filter('asDateTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY HH:mm');
    }
})
.filter('asDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY');
    }
})
.filter('asShortDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM');
    }
})
.filter('asTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('HH:mm');
    }
})
.filter('asMomentFormat', function ($filter) {
    return function (data, format) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format(format);
    }
})
.filter('asAutoFormat', function ($filter) {
    return function (data, key) {
        var value = data[key];
        if (!value) return value;
        var result = moment(value);
        if (aux.endswith(key, 'Date')) {
            return result.format('DD.MM.YYYY');
        } else if (aux.endswith(key, 'DateTime')) {
            return result.format('DD.MM.YYYY HH:mm');
        } else if (aux.endswith(key, 'Time')) {
            return result.format('HH:mm');
        } else {
            if (result.isValid()) {
                return result.toISOString();
            } else {
                return value;
            }
        }
    }
})
.filter('join', function ($filter) {
    return function (data, char) {
        if (data instanceof Array)
            return data.join(char);
        return data
    }
})
.filter('event_type_filter', function() {
    return function(items, props) {
        var out = [];
        if (angular.isArray(items) && props) {
            items.forEach(function(item) {
                var itemMatches = false;
                var keys = Object.keys(props);
                for (var i = 0; i < keys.length; i++) {
                    var prop = keys[i];
                    var prop_id = props[prop]['id'];
                    if (item.id === prop_id) {
                        itemMatches = true;
                        break;
                    }
                }
                if (itemMatches) {
                    out.push(item);
                }
            });
        } else {
            // Let the output be the input untouched
            out = items;
        }
        return out;
    }
})
.filter('contract_filter', function() {
    return function(items, event_info) {
        var out = [];
        if (angular.isArray(items) && event_info) {
            var client_info = event_info.client;

            items.forEach(function(item) {
                var itemMatches = false;
                if (item.finance.id == event_info.event_type.finance.id && item.recipient.id == event_info.organisation.id){
                    item.specifications.forEach(function(spec){
                        if(spec.event_type_id == event_info.event_type.id){
                            itemMatches = true;
                        }
                    });
                    if (item.contingent && itemMatches){
                        item.contingent.forEach(function(cont){
                            if((!cont.sex || cont.sex == client_info.info.sex.id) &&
                               (!cont.org_id || cont.org_id == client_info.work_org_id) &&
                               (!cont.insurer_id || cont.insurer_id == client_info.compulsory_policy.insurer_id) &&
                                 (!cont.policyType_id || cont.policyType_id == client_info.compulsory_policy.policyType_id)){
                                itemMatches = true;
                                if (client_info.voluntary_policies.length > 0){
                                    itemMatches = false;
                                    client_info.voluntary_policies.forEach(function(vol_policy){
                                        if(!itemMatches && (!cont.insurer_id || cont.insurer_id == vol_policy.insurer_id) &&
                                            (!cont.policyType_id || cont.policyType_id == vol_policy.policyType_id)) {
                                            itemMatches = true;
                                        }
                                    });
                                }
                            }
                        });
                    }
                }

                if (event_info.set_date){
                    var item_begDate = new Date(item.begDate);
                    var item_endDate = new Date(item.endDate);
                    if (!(item_begDate <= event_info.set_date && item_endDate >= event_info.set_date)){
                        itemMatches = false;
                    }
                }
                if (itemMatches) {
                    out.push(item);
                }
            });
            if (out.length && out.indexOf(event_info.contract) == -1){
                event_info.contract = out[0];
            }
        }
        return out;
    }
})

// Services
.factory('RefBook', ['$http', '$rootScope', function ($http, $rootScope) {
    var RefBook = function (name) {
        this.name = name;
        this.objects = [];
        this.load();
    };
    RefBook.prototype.load = function () {
        var t = this;
        $http.get(rb_root + this.name)
        .success(function (data) {
            t.objects = data.result;
            $rootScope.$broadcast('rb_load_success_'+ t.name, {
                text: 'Загружен справочник ' + t.name
            });
        })
        .error(function (data, status) {
            $rootScope.$broadcast('load_error', {
                text: 'Ошибка при загрузке справочника ' + t.name,
                code: status,
                data: data,
                type: 'danger'
            });
        });
        return this;
    };
    RefBook.prototype.get = function (id) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].id == id) return this.objects[i];
        }
        return null;
    };
    RefBook.prototype.get_by_code = function (code) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].code == code) return this.objects[i];
        }
        return null;
    };
    return RefBook;
}])
.service('RefBookService', ['RefBook', function (RefBook) {
    var cache = {};
    this.get = function (name) {
        if (cache.hasOwnProperty(name)) {
            return cache[name];
        } else {
            return cache[name] = new RefBook(name);
        }
    }
}])
.factory('Settings', ['RefBookService', '$rootScope', function(RefBookService, $rootScope) {
    var Settings = function() {
        this.rb_dict = {};
        this.rb = RefBookService.get('Setting');
        if (this.rb.objects.length) {
            this.init();
        }
        var self = this;
        $rootScope.$on('rb_load_success_Setting', function() {
            self.init();
        });
    };

    Settings.prototype.init = function() {
        var d = this.rb && this.rb.objects || [];
        for (var i=0; i < d.length; i++) {
            this.rb_dict[d[i].path] = d[i].value;
        }
    };

    Settings.prototype.get_string = function(val, def) {
        if ($.isEmptyObject(this.rb_dict)) return null;
        var default_val = '';
        if (arguments.length > 1) {
            default_val = def;
        }
        return this.rb_dict[val] || default_val;
    };

    return Settings;
}])
.factory('PrintingService', ['$window', '$http', '$rootScope', function ($window, $http, $rootScope) {
    var PrintingService = function (context_type) {
        if (arguments.length >= 3) {
            this.target = arguments[2]
        } else {
            this.target = '_blank'
        }
        this.context_type = context_type;
        this.context = null;
        this.templates = [];
    };
    PrintingService.prototype.set_context = function (context) {
        if (context === this.context) return;
        var t = this;
        $http.get(url_print_templates + context + '.json')
        .success(function (data) {
            t.templates = data.result.sort(function (left, right) {
                return (left.code < right.code) ? -1 : (left.code > right.code ? 1 : 0)
            });
        })
    };
    PrintingService.prototype.print_template = function(template_data_list, separated) { // [ {template_id, context}, ... ]
        var self = this;
        var send_data = {
            separated: separated,
            documents: template_data_list.map(function (item) {
                return {
                    id: item.template_id,
                    context_type: self.context_type,
                    context: angular.extend(
                        {}, item.context, {
                            'currentOrgStructure': "",
                            'currentOrganisation': 3479,
                            'currentPerson': current_user_id
                        }
                    )
                }
            }
        )};
        return $http.post(url_print_template, send_data)
        .success(function (data) {
            var w = $window.open();
            w.document.open();
            w.document.write(data);
            w.document.close();
            w.print();
        })
        .error(function (data, status) {
            $rootScope.$broadcast('printing_error', {
                text: 'Ошибка соединения с сервером печати',
                code: status,
                data: data,
                type: 'danger'
            })
        })
    };
    return PrintingService;
}])
.factory('WMAction', ['$http', '$rootScope', function ($http, $rootScope) {
    var Action = function () {
        this.action = null;
        this.action_culumns = {};
        this.event_id = null;
        this.action_type_id = null;
    };
    function success_wrapper(t) {
        return function (data) {
            angular.extend(t, data.result);
            t.action_columns = {
                assignable: false,
                unit: false
            };
            angular.forEach(data.result.properties, function (item) {
                t.action_columns.assignable |= item.type.is_assignable;
                t.action_columns.unit |= item.type.unit;
            });
            $rootScope.$broadcast('action_loaded', t);
        }
    }
    Action.prototype.get = function (id) {
        var t = this;
        return $http.get(url_action_get, {
            params: {
                action_id: id
            }
        }).success(success_wrapper(t));
    };
    Action.prototype.get_new = function (event_id, action_type_id) {
        this.event_id = event_id;
        this.action_type_id = action_type_id;
        var t = this;
        return $http.get(url_action_new, {
            params: {
                action_type_id: action_type_id,
                event_id: event_id
            }
        }).success(success_wrapper(t));
    };
    Action.prototype.save = function () {
        var t = this;
        $http.post(url_action_save, this).success(success_wrapper(t));
        return this;
    };
    Action.prototype.cancel = function () {
        if (this.action.id) {
            this.get(this.action.id)
        } else {
            this.get_new(this.event_id, this.action_type_id)
        }
    };
    return Action;
}])
.factory('EventType', ['RefBook', function (RefBook) {
    var EventType = function () {
        RefBook.call(this, 'EventType')
    };

    EventType.prototype = new RefBook('EventType');
    EventType.prototype.get_finances_by_rt = function(rt_id) {
        return this.get_filtered_by_rt(rt_id).map(function(el) {
            return el.finance;
        }).filter(function(el) {
            return el !== undefined && el != null;
        });
    };
    EventType.prototype.get_filtered_by_rt = function(rt_id) {
        return this.objects.filter(function(el) {
            return el.request_type && el.request_type.id === rt_id;
        });
    };
    EventType.prototype.get_filtered_by_rtf = function(rt_id, fin_id) {
        return this.objects.filter(function(el) {
            return el.request_type && el.finance &&
                el.request_type.id === rt_id && el.finance.id === fin_id;
        });
    };
    return EventType;
    }
])
// end services
.directive('uiMkb', function ($timeout, RefBookService) {
    return {
        restrict: 'E',
        require: '?ngModel',
        template:
            '<button class="btn btn-default btn-block" ng-click="to_show()">[[ $model.$modelValue.code ]] <span class="caret"></span></button>' +
            '<div class="well well-sm popupable" ng-show="shown" ng-mouseleave="to_hide_delay()" ng-mouseenter="to_hide_cancel()">' +
                '<input type="text" ng-model="query" class="form-control" />' +
                '<table class="table table-condensed table-hover table-clickable">' +
                    '<thead><tr><th>Код</th><th>Наименование</th></tr></thead>' +
                    '<tbody>' +
                        '<tr ng-repeat="row in $RefBook.objects | filter:query | limitTo:100" ng-click="onClick(row)">' +
                            '<td ng-bind="row.code"></td><td ng-bind="row.name"></td>' +
                        '</tr>' +
                    '</tbody>' +
                '</table>' +
            '</div>',
        scope: {},
        link: function (scope, element, attributes, ngModel) {
            scope.$model = ngModel;
            scope.$RefBook = RefBookService.get('MKB');
            var input_elem = $(element[0][0]);
            var div_elem = $(element[0][1]);
            var timeout = null;
            scope.shown = false;
            scope.query='';
            scope.to_show = function () {
                if (ngModel.$modelValue) {
                    scope.query = ngModel.$modelValue.code;
                } else {
                    scope.query = '';
                }
                div_elem.width(input_elem.width());
                scope.shown = true;
            };
            scope.to_hide_delay = function () {
                if (!timeout) {
                    timeout = $timeout(to_hide, 600)
                }
            };
            scope.to_hide_cancel = function () {
                if (timeout) {
                    $timeout.cancel(timeout);
                    timeout = null;
                }
            };
            scope.onClick = function (row) {
                ngModel.$setViewValue(row);
                to_hide();
            };
            scope.search = function (actual, expected) {
                return actual.split(' ').filter(function (part) {
                    return aux.startswith(part, expected)
                }).length > 0;
            };
            function to_hide () {
                timeout = null;
                scope.shown = false;
            }
        }
    };
})
.directive('uiScheduleTicket', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        scope: {
            day: '=day',
            showName: '=showName',
            ticket: '=uiScheduleTicket'
        },
        link: function (scope, element, attributes) {
            var elem = $(element);
            elem.addClass('btn btn-block');
            scope.$watch('ticket.status', function (n, o) {
                if (!scope.ticket) {
                    elem.addClass('disabled');
                    elem.html('&nbsp');
                    return
                }
                var text = '';
                switch (scope.ticket.attendance_type.code) {
                    case 'planned': text = moment(scope.ticket.begDateTime).format('HH:mm'); break;
                    case 'CITO': text = 'CITO'; break;
                    case 'extra': text = 'Сверх плана'; break;
                }
                if (n == 'busy') {
                    elem.removeClass('btn-success btn-warning btn-gray disabled');
                    elem.addClass('btn-danger');
                    if (scope.showName) {
                        text += ' - ' + scope.ticket.client
                    }
                } else {
                    elem.removeClass('btn-danger');
                    switch (scope.ticket.attendance_type.code) {
                        case 'planned': elem.addClass('btn-success'); break;
                        case 'CITO': elem.addClass('btn-warning'); break;
                        case 'extra': elem.addClass('btn-gray'); break;
                    }
                    var now = moment();
                    if (scope.day.roa ||
                        scope.ticket.begDateTime && (moment(scope.ticket.begDateTime) < now) ||
                                                     moment(scope.day.date) < now.startOf('day')) {
                        elem.addClass('disabled');
                    }
                }
                elem.text(text);
            });

        }
    };
}])
.directive('uiActionProperty', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        replace: true,
        link: function (scope, element, attributes) {
            var property = scope.$property = scope.$eval(attributes.uiActionProperty);
            var typeName = property.type.type_name;
            var element_code = null;
            switch (typeName) {
                case 'Text':
                case 'Html':
                case 'Жалобы':
                case 'Constructor':
                    element_code = '<textarea ckeditor="ckEditorOptions" ng-model="$property.value"></textarea>';
                    break;
                case 'Date':
                    element_code = '<input type="text" class="form-control" datepicker-popup="dd-MM-yyyy" ng-model="$property.value" />';
                    break;
                case 'Integer':
                case 'Double':
                case 'Time':
                    element_code = '<input class="form-control" type="text" ng-model="$property.value">';
                    break;
                case 'String':
                    if (property.type.domain) {
                        element_code = '<select class="form-control" ng-model="$property.value" ng-options="val for val in $property.type.values"></select>'
                    } else {
                        element_code = '<input class="form-control" type="text" ng-model="$property.value">';
                    }
                    break;
                default:
                    element_code = '<span ng-bind="$property.value">';
            }
            var el = angular.element(element_code);
            $(element[0]).append(el);
            $compile(el)(scope);
        }
    }
}])
.directive('wmTime', ['$document',
    function ($document) {
        return {
            restrict: 'E',
            replace: true,
            scope: {
                id: '=',
                name: '=',
                ngModel: '=',
                ngRequired: '=',
                ngDisabled: '='
            },
            templateUrl: "_timePicker.html",
            link: function(scope, element, attr){
                scope.isPopupVisible = false;
                scope.open_timepicker_popup = function(){
                    scope.isPopupVisible = !scope.isPopupVisible;
                }

                $document.bind('click', function(event){
                    var isClickedElementChildOfPopup = element
                      .find(event.target)
                      .length > 0;

                    if (isClickedElementChildOfPopup)
                      return;

                    scope.isPopupVisible = false;
                    scope.$apply();
                  });
            }

        };
    }
])
.directive('showTime', function() {
  return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, element, attrs, ngModel) {
          ngModel.$parsers.unshift(function (value) {
              var oldValue = ngModel.$modelValue;
              if (value && !(value instanceof Date)){
                   if ( /^([01]\d|2[0-3]):([0-5]\d)$/.test(value)){
                       var parts = value.split(':');
                       oldValue.setHours(parts[0]);
                       oldValue.setMinutes(parts[1]);
                   }
                   if (moment(oldValue).isValid()) {
                        ngModel.$setValidity('date', true);
                        ngModel.$setViewValue(oldValue);
                        return oldValue;
                   } else {
                        ngModel.$setValidity('date', false);
                        return undefined;
                   }
              }else{
                  return oldValue;
              }
          });

          if(ngModel) {
              ngModel.$formatters.push(function (value) {
                  if (!(value instanceof Date) && value) {
                      value = new Date(value);
                  }
                  if (value && moment(value).isValid()) {
                      return value.getHours() + ":" + value.getMinutes();
                  } else {
                      return undefined;
                  }
              });

      }
    }
  };
})
.directive('wmCustomDropdown', function ($timeout) {
    return {
        restrict: 'A',
        scope: {},
        link: function (scope, element) {
            var element_control = $($(element).find('*[wm-cdd-control]')[0]);
            var element_input = $($(element).find('*[wm-cdd-input]')[0]);
            if (!element_control[0]) {
                element_control = element_input;
                console.info('assuming element with wm-cdd-input is also wm-cdd-contol');
            }
            if (!element_input[0]) {
                throw 'wmCustomDropdown directive must have an element with wm-cdd-input attribute'
            }
            element_input.focusin(show_popup);
            element_input.click(show_popup);
            var element_popup = $($(element).find('*[wm-cdd-popup]')[0]);
            if (!element_input[0]) {
                throw 'wmCustomDropdown directive must have an element with wm-cdd-popup attribute'
            }
            element_popup.addClass('wm-popup');
            element_popup.mouseenter(show_popup);
            element_popup.mouseleave(hide_popup);
            var hide_timeout = null;
            function ensure_timeout_killed () {
                if (hide_timeout) {
                    $timeout.cancel(hide_timeout);
                    hide_timeout = null;
                }
            }
            var hide_popup_int = scope.hide_popup = function () {
                ensure_timeout_killed();
                element_popup.hide();
            };
            function show_popup () {
                ensure_timeout_killed();
                element_popup.width(Math.max(element_control.width(), element_popup.width()));
                element_popup.show();
            }
            function hide_popup () {
                ensure_timeout_killed();
                hide_timeout = $timeout(hide_popup_int, element_popup.attr.wmCddPopup || 600);
            }
        }
    }
})
.directive('wmSlowChange', function ($timeout) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, element, attr, ngModel) {
            var query_timeout = null;
            function ensure_timeout_killed () {
                if (query_timeout) {
                    $timeout.cancel(query_timeout);
                    query_timeout = null;
                }
            }
            ngModel.$viewChangeListeners.push(function () {
                ensure_timeout_killed();
                query_timeout = $timeout(function () {
                    scope.$eval(attr.wmSlowChange)
                }, attr.wmSlowChangeTimeout || 600)
            });
        }
    }
})
.directive('wmPageHeader', function ($timeout) {
    return {
        link: function (scope, element, attr) {
            if (window.opener){
                element.prepend('<div class="pull-right"><button class="btn btn-danger" onclick="window.opener.focus();window.close();" title="Закрыть"><span class="glyphicon glyphicon-remove"></span></button></div>');
            }
        }
    }
})
.directive("freeInputSelect", [
    '$compile', function($compile) {
      return {
        restrict: "A",
        scope: {
          items: '=',
          disabled: '=ngDisabled',
          freetext: '@',
          builder: '=',
          "class": '@'
        },
        require: '?ngModel',
        replace: true,
        template: function(el) {
          var itemTpl, template;
          itemTpl = el.html();
          return template = "<div class='fs-select fs-widget-root'>\n  <div ng-hide=\"active\" class=\"fs-select-sel\" ng-class=\"{'btn-group': item}\">\n      <a class=\"btn btn-default fs-select-active\"\n         ng-class='{\"btn-danger\": invalid}'\n         href=\"javascript:void(0)\"\n         ng-click=\"active = true\"\n         ng-disabled=\"disabled\">\n           <span ng-show='item'>" + itemTpl + "</span>\n           <span ng-hide='item'>none</span>\n      </a>\n      <button type=\"button\"\n              class=\"btn btn-default fs-select-clear-btn\"\n              aria-hidden=\"true\"\n              ng-show='item'\n              ng-disabled=\"disabled\"\n              ng-click='unselectItem()'>&times;</button>\n    </div>\n  <div class=\"open\" ng-show=\"active\">\n    <input class=\"form-control\"\n           fs-input\n           fs-focus-when='active'\n           fs-blur-when='!active'\n           fs-on-focus='active = true'\n           fs-on-blur='onBlur()'\n           fs-hold-focus\n           fs-down='move(1)'\n           fs-up='move(-1)'\n           fs-pg-up='move(-11)'\n           fs-pg-down='move(11)'\n           fs-enter='onEnter($event)'\n           fs-esc='active = false'\n           type=\"text\"\n           placeholder='Search'\n           ng-model=\"search\"\n           fs-null-form />\n\n    <div ng-if=\"active && dropdownItems.length > 0\">\n      <div fs-list items=\"dropdownItems\">\n       " + itemTpl + "\n      </div>\n    </div>\n  </div>\n</div>";
        },
        controller: function($scope, $element, $attrs, $filter, $timeout) {
          var updateDropdown;
          $scope.active = false;
          if ($attrs.freetext != null) {
            $scope.dynamicItems = function() {
              if ($scope.search) {
                var free_input = $scope.builder($scope.search);
                return [free_input];
              } else {
                return [];
              }
            };
          } else {
            $scope.dynamicItems = function() {
              return [];
            };
          }
          updateDropdown = function() {
            return $scope.dropdownItems = $filter('filter')($scope.items, $scope.search).concat($scope.dynamicItems());
          };
          $scope.$watch('active', function(q) {
            return updateDropdown();
          });
          $scope.$watch('search', function(q) {
            return updateDropdown();
          });
          $scope.selectItem = function(item) {
            $scope.item = item;
            $scope.search = "";
            return $scope.active = false;
          };
          $scope.unselectItem = function(item) {
            return $scope.item = null;
          };
          $scope.onBlur = function() {
            return $timeout(function() {
              $scope.active = false;
              return $scope.search = '';
            }, 0, true);
          };
          $scope.move = function(d) {
            return $scope.listInterface.move && $scope.listInterface.move(d);
          };
          $scope.onEnter = function(event) {
            if ($scope.dropdownItems.length > 0) {
              return $scope.selectItem($scope.listInterface.selectedItem);
            } else {
              return $scope.selectItem(null);
            }
          };
          return $scope.listInterface = {
            onSelect: function(selectedItem) {
              return $scope.selectItem(selectedItem);
            },
            move: function() {
              return console.log("not-implemented listInterface.move() function");
            }
          };
        },
        link: function(scope, element, attrs, ngModelCtrl, transcludeFn) {
          if (ngModelCtrl) {
            scope.$watch('item', function(newValue, oldValue) {
              if (newValue !== oldValue) {
                return ngModelCtrl.$setViewValue(scope.item);
              }
            });
            return ngModelCtrl.$render = function() {
              return scope.item = ngModelCtrl.$viewValue;
            };
          }
        }
      };
    }
  ]);

var aux = {
    getQueryParams: function (qs) {
        qs = qs.split("+").join(" ");

        var params = {}, tokens,
                re = /[?&]?([^=]+)=([^&]*)/g;

        while (tokens = re.exec(qs)) {
            params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
        }

        return params;
    },
    range: function (num) {
        return Array.apply(null, new Array(num)).map(function(_, i) {return i;})
    },
    moment: moment,
    months: [
        {name: 'Январь', value: 0},
        {name: 'Февраль', value: 1},
        {name: 'Март', value: 2},
        {name: 'Апрель', value: 3},
        {name: 'Май', value: 4},
        {name: 'Июнь', value: 5},
        {name: 'Июль', value: 6},
        {name: 'Август', value: 7},
        {name: 'Сентябрь', value: 8},
        {name: 'Октябрь', value: 9},
        {name: 'Ноябрь', value: 10},
        {name: 'Декабрь', value: 11}
    ],
    endswith: function (str, suffix) {
        return str.indexOf(suffix, str.length - suffix.length) !== -1;
    },
    startswith: function (str, prefix) {
        return str.indexOf(prefix) === 0;
    },
    format: function (record, key) {
        if (typeof (record) === 'undefined') {
            return null;
        } else if (aux.endswith(key, 'DateTime')) {
            return moment(record[key]).format('DD-MM-YYYY HH:mm');
        } else if (aux.endswith(key, 'Date')) {
            return moment(record[key]).format('DD-MM-YYYY');
        } else {
            return record[key];
        }
    },
    arrayCopy: function (source) {
        // proven fastest copy mechanism http://jsperf.com/new-array-vs-splice-vs-slice/28
        var b = [];
        var i = source.length;
        while (i--) {b[i] = source[i]}
        return b;
    },
    func_in: function (against) {
        return function (item) {
            return against.indexOf(item) !== -1;
        }
    },
    func_not_in: function (against) {
        return function (item) {
            return against.indexOf(item) === -1;
        }
    },
    find_by_code: function (where, code, field) {
        if (typeof (field) === 'undefined') field = 'code';
        var subresult = where.filter(function (item) {return item[field] == code});
        if (subresult.length === 0) return null;
        return subresult[0]
    },
    inArray: function (array, item) {
        return array.indexOf(item) !== -1;
    },
    removeFromArray: function (array, item) {
        if (aux.inArray(array, item))
            array.splice(array.indexOf(item), 1)
    },
    forEach: function (object, callback) {
        var result = {};
        var key;
        for (key in object) {
            result[key] = callback(object[key]);
        }
        return result
    }
};
if (!HTMLElement.prototype.hasOwnProperty('getOffsetRect')) {
    HTMLElement.prototype.getOffsetRect = function () {
        // (1)
        var box = this.getBoundingClientRect();
        // (2)
        var body = document.body;
        var docElem = document.documentElement;
        // (3)
        var scrollTop = window.pageYOffset || docElem.scrollTop || body.scrollTop;
        var scrollLeft = window.pageXOffset || docElem.scrollLeft || body.scrollLeft;
        // (4)
        var clientTop = docElem.clientTop || body.clientTop || 0;
        var clientLeft = docElem.clientLeft || body.clientLeft || 0;
        // (5)
        var top  = box.top +  scrollTop - clientTop;
        var left = box.left + scrollLeft - clientLeft;
        return { top: Math.round(top), left: Math.round(left) }
    }
}