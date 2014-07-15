/**
 * Created by mmalkov on 15.07.14.
 */
angular.module('WebMis20.directives.goodies', [])
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
});
