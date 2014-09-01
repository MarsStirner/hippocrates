/**
 * Created by mmalkov on 04.08.14.
 */
'use strict';

angular.module('WebMis20.ActionLayout', ['WebMis20.validators', 'WebMis20.directives.personTree', 'WebMis20.directives.wysiwyg'])
.directive('wmActionLayout', ['$compile', 'SelectAll', function ($compile, SelectAll) {
    return {
        restrict: 'E',
        scope: {
            action: '='
        },
        link: function (scope, element) {
            var current_element = element;
            var v_groups_count = 0; // Must be set to zero before complete rebuild

            function build(tag) {
                var context = arguments[1];
                var inner_template;
                switch (tag.tagName) {

                    case 'ap':
                        if (tag.children && tag.children.length) {console.log('"ap" tags don\'t support children');}
                        var property = scope.action.get_property(tag.id);
                        if (property === undefined) return '{' + tag.id + '}';
                        var property_code = 'action.get_property(' + tag.id + ')';

                        switch (property.type.type_name) {
                            case 'Constructor':
                                inner_template = '<wysiwyg ng-model="{0}.value" thesaurus-code="{1}" />'.format('{0}', property.type.domain);
                                sas.select(tag.id, false);
                                break;
                            case 'Text':
                            case 'Html':
                            case 'Жалобы':
                                inner_template = '<wysiwyg ng-model="{0}.value" />';
                                sas.select(tag.id, false);
                                break;
                            case 'Date':
                                inner_template = '<input type="text" class="form-control" datepicker-popup="dd-MM-yyyy" ng-model="{0}.value" />';
                                break;
                            case 'Integer':
                                inner_template = '<input class="form-control" type="number" ng-model="{0}.value" valid-number valid-number-negative>';
                                break;
                            case 'Double':
                                inner_template = '<input class="form-control" type="number" ng-model="{0}.value" valid-number valid-number-negative valid-number-float>';
                                break;
                            case 'Time':
                                inner_template = '<div fs-time ng-model="{0}.value"></div>';
                                break;
                            case 'String':
                                if (property.type.domain) {
                                    inner_template = '<select class="form-control" ng-model="{0}.value" ng-options="val for val in {0}.type.values"></select>'
                                } else {
                                    inner_template = '<input class="form-control" type="text" ng-model="{0}.value">';
                                }
                                break;
                            case 'JobTicket':
                                inner_template = '<span ng-bind="{0}.value.datetime | asDateTime"></span>';
                                break;
                            case 'AnalysisStatus':
                                inner_template = '<rb-select ref-book="rbAnalysisStatus" ng-model="{0}.value"></rb-select>';
                                break;
                            case 'OperationType':
                                inner_template = '<rb-select ref-book="rbOperationType" ng-model="{0}.value"></rb-select>';
                                break;
                            case 'HospitalBedProfile':
                                inner_template = '<rb-select ref-book="rbHospitalBedProfile" ng-model="{0}.value"></rb-select>';
                                break;
                            case 'Person':
                                inner_template = '<wm-person-select ng-model="{0}.value"></wm-person-select>';
                                break;
                            case 'Organisation':
                                inner_template =
                                    '<ui-select ng-model="{0}.value" theme="select2" class="form-control" autocomplete="off" ref-book="Organisation">\
                                        <ui-select-match placeholder="не выбрано">[[ $select.selected.full_name ]]</ui-select-match>\
                                        <ui-select-choices repeat="item in $refBook.objects | filter: $select.search | limitTo: 50">\
                                            <span ng-bind-html="item.full_name | highlight: $select.search"></span>\
                                        </ui-select-choices>\
                                    </ui-select>';
                                break;
                            case 'MKB':
                                inner_template = '<ui-mkb ng-model="{0}.value"></ui-mkb>';
                                break;
                            case 'OrgStructure': // Без фильтров
                                inner_template =
                                    '<wm-custom-dropdown ng-model="{0}.value">\
                                        <wm-org-structure-tree></wm-org-structure-tree>\
                                    </wm-custom-dropdown>';
                                break;
                            case 'ReferenceRb':
                                var domain = property.type.domain.split(';'),
                                    rbTable = domain[0],
                                    rb_codes = domain[1].split(',').map(function (code) {
                                        return "'{0}'".format(code.trim());
                                    }).filter(function (code) {
                                        return code !== "''";
                                    }),
                                    extra_filter = rb_codes.length ? 'attribute:\'code\':[{0}]'.format(rb_codes.join(',')) : '';
                                inner_template = '<rb-select ref-book="{1}" ng-model="{0}.value" extra-filter="{2}"></rb-select>'.format('{0}', rbTable, extra_filter);
                                break;
                            case 'Diagnosis':
                                inner_template = '<wm-diagnosis ng-model="{0}.value" add-new="true"></wm-diagnosis>';
                                break;
                            default:
                                inner_template = '<span ng-bind="{0}.value"></span>';
                        }
                        var property_name = tag.title || property.type.name;
                        var template;
                        if (context === undefined) {
                            template = '<div class="row">\
                            <div class="col-sm-3">\
                                <wm-checkbox select-all="sas" key="{2}">{0}</wm-checkbox>\
                            </div>\
                            <div class="col-sm-9"><div ng-show="sas.selected({2})">{1}</div></div>\
                        </div>'.format(
                                property_name,
                                inner_template.format(property_code),
                                property.type.id
                            );
                        } else {
                            if (context.tag.tagName == 'table') {
                                template = '<tr>\
                                    <td><label><input type="checkbox" ng-model="{1}.is_assigned">{0}</label></td>\
                                    <td>{2}</td>\
                                    <td>{3}</td>\
                                </tr>'.format(
                                    property_name,
                                    property_code,
                                    inner_template.format(property_code),
                                    property.type.unit.code
                                );
                            } else if (context.tag.tagName == 'vgroup') {
                                template = '<div class="row">\
                                    <div class="col-sm-3">\
                                        <label><input type="checkbox" ng-model="{1}.is_assigned">{0}</label>\
                                    </div>\
                                    <div class="col-sm-9"><div ng-show="sas.selected({2})">{1}</div></div>\
                                </div>'.format(
                                    property_name,
                                    property_code,
                                    inner_template.format(property_code),
                                    property.type.id
                                );
                            }
                        }
                        return template;

                    case 'vgroup':
                        var title = tag.title;
                        inner_template = tag.children.map(function (child) {
                            return '<li class="list-group-item">{0}</li>'.format(build(child, {tag: tag}))
                        }).join('');
                        var result =  '<div class="panel panel-default">\
                                <div class="panel-heading"><label><wm-checkbox select-all="sas_vgroup" key="{2}" />{0}</label></div>\
                                <ul class="list-group" ng-show="sas_vgroup.selected({2})">\
                                    {1}\
                                </ul>\
                            </div>'.format(title, inner_template, v_groups_count);
                        v_groups_count++;
                        return result;

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

                    case 'table':
                        return '<table class="table table-condensed">{0}</table>'.format(tag.children.map(function (child) {
                            if (child.tag.tagName != 'ap') {throw '"table" tags only support "ap" children';}
                            return build(child, {tag: tag});
                        }).join(''));

                    case 'root':
                        inner_template = tag.children.map(function (child) {
                            return '<div class="col-md-12">{0}</div>'.format(build(child))
                        }).join('');
                        return '<div class="row marginal">{0}</div>'.format(inner_template);

                    default:
                        return '<div>[[ tag | json ]]</div>';
                }
            }

            var sas = scope.sas = new SelectAll([]);
            var sas_vgroup = scope.sas_vgroup = new SelectAll([]);

            scope.$watch('action.action.properties', function (properties, old) {
                if (angular.equals(properties, old)) return;
                properties = properties || [];
                sas.setSource(properties.map(function (item) {return item.type.id}));
            });

            scope.ckEditorOptions = {
                language: 'ru',
                removeButtons: '',
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
                v_groups_count = 0;
                var template = build(layout);
                sas_vgroup.setSource(aux.range(v_groups_count));
                sas_vgroup.selectAll();
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
