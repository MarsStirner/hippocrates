/**
 * Created by mmalkov on 04.08.14.
 */
'use strict';

angular.module('WebMis20.ActionLayout', [])
.directive('wmActionLayout', ['$compile', 'SelectAll', function ($compile, SelectAll) {
    return {
        restrict: 'E',
        scope: {
            action: '='
        },
        link: function (scope, element, attributes, ctrl) {
            var original_element = element,
                current_element = element;

            function build(tag) {
                var inner_template;
                switch (tag.tagName) {

                    case 'ap':
                        var property = scope.action.get_property(tag.id);
                        if (property === undefined) return '{' + tag.id + '}';
                        var property_code = 'action.get_property(' + tag.id + ')';

                        switch (property.type.type_name) {
                            case 'Text':
                            case 'Html':
                            case 'Жалобы':
                            case 'Constructor':
                                inner_template = '<textarea ckeditor="ckEditorOptions" ng-model="{0}.value"></textarea>';
                                break;
                            case 'Date':
                                inner_template = '<input type="text" class="form-control" datepicker-popup="dd-MM-yyyy" ng-model="{0}.value" />';
                                break;
                            case 'Integer':
                            case 'Double':
                                inner_template = '<input class="form-control" type="text" ng-model="{0}.value">';
                                break;
                            case 'Time':
                                inner_template = '<div fs-time ng-model="{0}.value">';
                                break;
                            case 'String':
                                if (property.type.domain) {
                                    inner_template = '<select class="form-control" ng-model="{0}.value" ng-options="val for val in {0}.type.values"></select>'
                                } else {
                                    inner_template = '<input class="form-control" type="text" ng-model="{0}.value">';
                                }
                                break;
                            default:
                                inner_template = '<span ng-bind="{0}.value"></span>';
                        }
                        var property_name = tag.title || property.type.name;
                        return '<div class="row">\
                            <div class="col-sm-3">\
                                <wm-checkbox select-all="sas" key="{2}">{0}</wm-checkbox>\
                            </div>\
                            <div class="col-sm-9"><div ng-show="sas.selected({2})">{1}</div></div>\
                        </div>'
                        .format(
                            property_name,
                            inner_template.format(property_code),
                            property.type.id
                        );

                    case 'vgroup':
                        var title = tag.title;
                        inner_template = tag.children.map(function (child) {
                            return '<li class="list-group-item">{0}</li>'.format(build(child))
                        }).join('');
                        return '<div class="panel panel-default">\
                                <div class="panel-heading">{0}</div>\
                                <ul class="list-group">\
                                    {1}\
                                </ul>\
                            </div>'.format(title, inner_template);

                    case 'row':
                        var valid_cols = [1, 2, 3, 4, 6, 12],
                            col_widths = [12, 6, 4, 3, 2, 1],
                            w;
                        if (valid_cols.has(tag.cols)) {
                            w = col_widths[valid_cols.indexOf(tag.cols)];
                        } else {
                            throw 'Incorrect cols number'
                        }
                        inner_template = tag.children.map(function (child) {
                            return '<div class="col-md-{0}">{1}</div>'.format(w, build(child))
                        }).join('');
                        return '<div class="row">{0}</div>'.format(inner_template);

                    case 'root':
                        inner_template = tag.children.map(function (child) {
                            return '<div class="col-md-12">{0}</div>'.format(build(child))
                        }).join('');
                        return '<div class="row">{0}</div>'.format(inner_template);

                    default:
                        return '<div>[[ tag | json ]]</div>';
                }
            }

            var sas = scope.sas = new SelectAll([]);

            scope.$watch('action.action.properties', function (properties, old) {
                if (angular.equals(properties, old)) return;
                properties = properties || [];
                sas.setSource(properties.map(function (item) {return item.type.id}));
            });

            scope.ckEditorOptions = {
                language: 'ru',
                toolbar: [
                    { name: 'document', items: [ 'Source', '-', 'NewPage', 'Preview', '-', 'Templates' ] },	// Defines toolbar group with name (used to create voice label) and items in 3 subgroups.
                    [ 'Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo' ],			// Defines toolbar group without name.
                    { name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline' ] }
                ],
                autoGrow_minHeight: 50,
                autoGrow_bottomSpace: 50,
                autoGrow_onStartup: true,
                height: 100,
                autoParagraph: false
            };

            scope.$watch('action.layout', function (layout) {
                var template = build(layout);
                var replace = $(template);
                $(current_element).replaceWith(replace);
                current_element = replace;
                $compile(replace)(scope);
                return layout;
            })
        }
    }
}])
;
