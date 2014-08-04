/**
 * Created by mmalkov on 04.08.14.
 */
'use strict';

angular.module('WebMis20.ActionLayout', [])
.service('ActionLayoutService', function () {

})
.directive('uiActionProperty', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        replace: true,
        scope: {
            $property: '=uiActionProperty'
        },
        link: function (scope, element, attributes) {
            var element_code = null;
            switch (scope.$property.type.type_name) {
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
                    if (scope.$property.type.domain) {
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
.directive('wmActionLayoutItem', ['$compile', function ($compile) {
    return {
        scope: {
            tag: '='
        },
        link: function (scope, element, attributes) {
            var template;
            switch (scope.tag.name) {
                case 'ap':
                    template = '<div ui-action-property="">'; // TODO: Это надо продумать!
                    break;
                case 'vgroup':
                    template =
                        '<div class="well well-sm">\
                            <div class="row" ng-repeat="child in tag.children">\
                                <div class="col-md-12">\
                                    <wm-action-layout-item tag="child"></wm-action-layout-item>\
                                </div>\
                            </div>\
                        </div>';
                    break;
                case 'row':
                    var c = [1, 2, 3, 4, 6, 12],
                        d = [12, 6, 4, 3, 2, 1],
                        w;
                    if (c.has(scope.tag.cols)) {
                        w = d[c.indexOf(scope.tag.cols)];
                    } else {
                        throw 'Incorrect cols number'
                    }
                    template =
                        '<div class="row">\
                            <div class="col-md-{0}" ng-repeat="child in tag.children">\
                                <wm-action-layout-item tag="child"></action-layout-item>\
                            </div>\
                        </div>'.format('' + w);
                    break;
                case 'root':
                    template =
                        '<div ng-repeat="child in tag.children">\
                            <wm-action-layout-item tag="child"></wm-action-layout>\
                        </div>';
                    break;
                default:
                    template = '<div>[[ tag | json ]]</div>'
            }
            var replace = $(template);
            $(element).replaceWith(replace);
            $compile(replace)(scope);
        }
    }
}])
;
