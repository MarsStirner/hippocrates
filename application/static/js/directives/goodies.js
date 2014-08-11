/**
 * Created by mmalkov on 15.07.14.
 */
angular.module('WebMis20.directives.goodies', [])
.factory('TimeoutCallback', ['$timeout', function ($timeout) {
    var Timeout = function (callback, timeout) {
        this.timeout = timeout;
        this.hideki = null;
        this.callback = callback;
    };
    Timeout.prototype.kill = function () {
        if (this.hideki) {
            $timeout.cancel(this.hideki)
        }
    };
    Timeout.prototype.start = function () {
        this.kill();
        this.hideki = $timeout(this.callback, this.timeout)
    };
    return Timeout;
}])
.directive('wmCustomDropdown', ['$timeout', '$compile', 'TimeoutCallback', function ($timeout, $compile, TimeoutCallback) {

    return {
        restrict: 'E',
        require: 'ngModel',
        scope: {
            onSelected: '&',
            wmTimeout: '@'
        },
        link: function (scope, original_element, attrs, ngModel) {
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
            var popupTimeoutObject = new TimeoutCallback(hide_popup, wmTimeout);
            var changeTimeoutObject = new TimeoutCallback(function () {
                scope.$broadcast('FilterChanged', scope.$query)
            }, 400);
            scope.$watch('$query', function (n, o) {
                if (angular.equals(n, o)) return n;
                changeTimeoutObject.start()
            });
            function hide_popup () {
                popupTimeoutObject.kill();
                element_popup.hide();
            }
            function show_popup () {
                popupTimeoutObject.kill();
                element_popup.width(element_control.width() - 20);
                element_popup.show();
            }
            element_input.focusin(show_popup);
            element_input.click(show_popup);
            element_popup.mouseenter(show_popup);
            element_popup.mouseleave(function() {popupTimeoutObject.start()});

            scope.$ctrl = {
                $set_query: function (query) {scope.$query = query},
                $select: function (item) {
                    ngModel.$setViewValue(item);
                    ngModel.$render();
                    if (scope.onSelected) scope.onSelected(item);
                    hide_popup();
                }
            };
            scope.$query = '';

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
