/**
 * Created by mmalkov on 15.07.14.
 */
angular.module('WebMis20.directives.goodies', [])
.directive('wmCustomDropdown', ['$timeout', '$compile', function ($timeout, $compile) {
    return {
        restrict: 'E',
        require: ['ngModel', 'wmCustomDropdown'],
        controller: ['$scope', function ($scope) {
            var listeners = [];
            this.clean = function () {listeners = []};
            this.add = function (listener) {listeners.push(listener)};
            this.select = function (item) {listeners.forEach(function (listener) {listener.call(null, item)})};
            this.setQuery = function (query) {$scope.$query = query};
        }],
        scope: {
            onSelected: '&',
            wmTimeout: '@'
        },
        link: function (scope, original_element, attrs, ctrls) {
            var wmTimeout = scope.wmTimeout || 600;
            // Templating...
            var element = $(original_element);
            var element_input = $('<input type="text" ng-model="$query" class="form-control">');
            var element_control = $('<div class="input-group"></div>');
            element_control.append('<span class="input-group-addon"><i class="glyphicon glyphicon-search"></i></span>');
            element_control.append(element_input);
            element_control.append('<span class="input-group-btn"><button class="btn btn-default" ng-click="$query=\'\'"><i class="glyphicon glyphicon-remove"></i></button></span>');
            var element_popup = $('<div class="wm-popup well well-sm"></div>');
            element_popup.append(element.html());
            var element_wrapper = $('<div style="display: inline"></div>');
            element_wrapper.append(element_control).append(element_popup);
            element.replaceWith(element_wrapper);

            // Handling popups...
            var hide_timeout = null;
            function ensure_timeout_killed () {
                if (hide_timeout) {
                    $timeout.cancel(hide_timeout);
                    hide_timeout = null;
                }
            }
            var hide_popup_int = function () {
                ensure_timeout_killed();
                element_popup.hide();
            };
            function show_popup () {
                ensure_timeout_killed();
                element_popup.width(Math.min(element_control.width() - 20, element_popup.width()));
                element_popup.show();
            }
            function hide_popup () {
                ensure_timeout_killed();
                hide_timeout = $timeout(hide_popup_int, wmTimeout);
            }
            element_input.focusin(show_popup);
            element_input.click(show_popup);
            element_popup.mouseenter(show_popup);
            element_popup.mouseleave(hide_popup);

            var ngModel = ctrls[0], ctrl = ctrls[1];
            scope.$query = '';
            ctrl.add(hide_popup_int);
            if (scope.onSelected) {ctrl.add(scope.onSelected)}
            scope.select = ctrl.select;

            $compile(element_wrapper)(scope);
        }
    }
}])
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
});
