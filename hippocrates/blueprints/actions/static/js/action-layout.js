/**
 * Created by mmalkov on 04.08.14.
 */
'use strict';

angular.module('WebMis20')
.directive('wmActionLayout', ['$compile', 'SelectAll', '$filter', '$log',
        function ($compile, SelectAll, $filter, $log) {
    return {
        restrict: 'E',
        scope: {
            action: '='
        },
        link: function (scope, element) {
            var current_element = element;
            var v_groups_count = 0; // Must be set to zero before complete rebuild
            scope.layout_tools = {
                format_Diagnosis: function (diag) {
                    return '{0}: {1} - {2}{ (|3|)}, {4} - {5}'.formatNonEmpty(
                        safe_traverse(diag, ['diagnosis_type', 'name']),
                        safe_traverse(diag, ['diagnosis', 'mkb', 'code']),
                        safe_traverse(diag, ['diagnosis', 'mkb', 'name']),
                        safe_traverse(diag, ['character', 'name']),
                        $filter('asDate')(diag.set_date),
                        $filter('asDate')(diag.end_date)
                    );
                },
                onCheckboxSelected: function (args) {
                    scope.$broadcast('actionLayoutItemFocused', {
                        apt_id: args
                    });
                },
                getValueNormStyle: function (prop) {
                    var s = {};
                    if (prop.value_in_norm === null) return s;

                    if (prop.value_in_norm < 0) {
                        s['color'] = 'blue';
                        s['font-weight'] = 'bold';
                    }
                    else if (prop.value_in_norm > 0) {
                        s['color'] = 'red';
                        s['font-weight'] = 'bold';
                    }
                    return s;
                },
                calcValueNorm: function (prop) {
                    var norm_min = prop.type.norm_min,
                        norm_max = prop.type.norm_max;
                    var v = Number(prop.value);
                    if (_.isNumber(v)) {
                        if (norm_min !== null && v < norm_min) prop.value_in_norm = -1;
                        else if (norm_max !== null && v > norm_max) prop.value_in_norm = 1;
                        else prop.value_in_norm = 0;
                    } else {
                        prop.value_in_norm = 0;
                    }
                }
            };
            scope.unity_function = function (arg) { return arg };

            function build(tag) {
                var context = arguments[1];
                var inner_template;
                switch (tag.tagName) {

                    case 'ap':
                        if (tag.children && tag.children.length) {$log('"ap" tags don\'t support children');}
                        var property = scope.action.get_property(tag.id);
                        if (property === undefined) return '{' + tag.id + '}';
                        var property_code = 'action.get_property(' + tag.id + ')',
                            property_value_domain_obj = property_code + '.type.domain_obj',
                            property_is_assignable = 'action.is_assignable(' + tag.id + ')',
                            property_unit_code = (property.type.unit)?(property.type.unit.code):('');

                        if (scope.action.readonly) {
                            switch (property.type.type_name) {
                                case 'Constructor':
                                case 'Text':
                                case 'Html':
                                case 'Жалобы':
                                    inner_template = '<span ng-bind-html="{0}.value | trustHtml" id="[[{0}.type.id]]"></span>'; break;
                                case 'String':
                                case 'String/Select':
                                case 'String/Free':
                                case 'Integer':
                                case 'Double':
                                    inner_template = '<span id="[[{0}.type.id]]"><span ng-style="{2}">[[ {0}.value ]]</span> {1}</span>'.format(
                                        '{0}', property.value !== null ? property_unit_code : '',
                                        'layout_tools.getValueNormStyle({0})'.format(property_code)); break;
                                case 'Date':
                                    inner_template = '<span ng-bind="{0}.value | asDate" id="[[{0}.type.id]]"></span>'; break;
                                case 'Time':
                                    inner_template = '<span ng-bind="{0}.value | asTime" id="[[{0}.type.id]]"></span>'; break;
                                case 'JobTicket':
                                    inner_template = '<span ng-bind="{0}.value.datetime | asDateTime" id="[[{0}.type.id]]"></span>'; break;
                                case 'AnalysisStatus':
                                case 'OperationType':
                                case 'HospitalBedProfile':
                                case 'ReferenceRb':
                                    inner_template = '<span ng-bind="{0}.value.name" id="[[{0}.type.id]]"></span>'; break;
                                case 'Person':
                                    inner_template = '<span ng-bind="{0}.value.name" id="[[{0}.type.id]]"></span>'; break;
                                case 'Organisation':
                                    inner_template = '<span ng-bind="{0}.value.full_name" id="[[{0}.type.id]]"></span>'; break;
                                case 'MKB':
                                    inner_template = '<span ng-bind="{0}.value.name" id="[[{0}.type.id]]"></span>'; break;
                                case 'OrgStructure':
                                    inner_template = '<span ng-bind="{0}.value.name" id="[[{0}.type.id]]"></span>'; break;
                                case 'Diagnosis':
                                    if (property.type.vector) {
                                        inner_template =
                                            '<div ng-repeat="$v in {0}.value" ng-bind="layout_tools.format_Diagnosis($v)"></div>';
                                    } else {
                                        inner_template =
                                            '<span ng-bind="layout_tools.format_Diagnosis({0}.value)"></span>';
                                    }
                                    break;
                                case 'URL':
                                    inner_template = scope.action.is_new() || !property.value ?
                                        '<span id="[[{0}.type.id]]"></span>' :
                                        '<a ng-href="[[{0}.value]]" target="_blank" title="Открыть ссылку в новой вкладке"\
                                            style="font-size:larger; margin-left: 10px; margin-top: 5px;"\
                                            id="[[{0}.type.id]]">[[ {0}.type.description || {0}.value ]]</a>';
                                    break;

                                default:
                                    inner_template = '<span ng-bind="{0}.value" id="[[{0}.type.id]]"></span>'; break;
                            }
                        } else {
                            switch (property.type.type_name) {
                                case 'Constructor':
                                    inner_template = '<wysiwyg ng-model="{0}.value" thesaurus-code="{1}"\
                                        id="[[{0}.type.id]]" al-item-focused placeholder="Введите текст" />'.format('{0}', property.type.domain);
                                    break;
                                case 'Text':
                                case 'Html':
                                case 'Жалобы':
                                    inner_template = '<wysiwyg ng-model="{0}.value" id="[[{0}.type.id]]" al-item-focused/>';
                                    break;
                                case 'Date':
                                    inner_template = '<wm-date ng-model="{0}.value" id="[[{0}.type.id]]" al-item-focused></wm-date>';
                                    break;
                                case 'Integer':
                                    inner_template = '<input class="form-control" type="text" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused valid-number valid-number-negative\
                                        ng-style="{1}" {2}>'.format('{0}', 'layout_tools.getValueNormStyle({0})'.format(property_code));
                                    if (property.type.unit) {
                                        inner_template = '<div class="input-group">{0}<span class="input-group-addon">{1}</span></div>'
                                            .format(inner_template, property_unit_code,
                                                property.type.norm ? 'ng-change="layout_tools.calcValueNorm({0})"'.format(property_code) : '');
                                    }
                                    break;
                                case 'Double':
                                    inner_template = '<input class="form-control" type="text" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused valid-number valid-number-negative valid-number-float\
                                        ng-style="{1}" {2}>'.format('{0}', 'layout_tools.getValueNormStyle({0})'.format(property_code));
                                    if (property.type.unit) {
                                        inner_template = '<div class="input-group">{0}<span class="input-group-addon">{1}</span></div>'
                                            .format(inner_template, property_unit_code,
                                                property.type.norm ? 'ng-change="layout_tools.calcValueNorm({0})"'.format(property_code) : '');
                                    }
                                    break;
                                case 'Time':
                                    inner_template = '<div fs-time ng-model="{0}.value" id="[[{0}.type.id]]" al-item-focused></div>';
                                    break;
                                case 'String':
                                    inner_template = '<input class="form-control" type="text" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused ng-style="{1}" {2}>'
                                        .format('{0}', 'layout_tools.getValueNormStyle({0})'.format(property_code),
                                                property.type.norm ? 'ng-change="layout_tools.calcValueNorm({0})"'.format(property_code) : '');
                                    if (property.type.unit) {
                                        inner_template = '<div class="input-group">{0}<span class="input-group-addon">{1}</span></div>'
                                            .format(inner_template, property_unit_code);
                                    }
                                    break;
                                case 'String/Select':
                                    inner_template =
                                        '<ui-select ng-model="{0}.value" theme="select2" class="form-control" autocomplete="off"\
                                                id="[[{0}.type.id]]" al-item-focused no-undefined-value>\
                                            <ui-select-match placeholder="не выбрано" allow-clear="true">[[ $select.selected ]]</ui-select-match>\
                                            <ui-select-choices repeat="item in {0}.type.domain_obj.values | filter: $select.search">\
                                                <span ng-bind-html="item | highlight: $select.search"></span>\
                                            </ui-select-choices>\
                                        </ui-select>';
                                    break;
                                case 'String/Free':
                                    inner_template =
                                        '<ui-select ng-model="{0}.value" theme="select2" class="form-control" tagging="unity_function"\
                                                autocomplete="off" id="[[{0}.type.id]]" al-item-focused no-undefined-value>\
                                            <ui-select-match placeholder="не выбрано" allow-clear="true">[[ $select.selected ]]</ui-select-match>\
                                            <ui-select-choices repeat="item in [].concat({0}.type.domain_obj.values, \'\') | filter: $select.search">\
                                                <span ng-bind-html="item | highlight: $select.search"></span>\
                                            </ui-select-choices>\
                                        </ui-select>';
                                    break;
                                case 'JobTicket':
                                    inner_template = '<span ng-bind="{0}.value.datetime | asDateTime"></span>';
                                    break;
                                case 'AnalysisStatus':
                                    inner_template = '<rb-select ref-book="rbAnalysisStatus" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused></rb-select>';
                                    break;
                                case 'OperationType':
                                    inner_template = '<rb-select ref-book="rbOperationType" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused></rb-select>';
                                    break;
                                case 'HospitalBedProfile':
                                    inner_template = '<rb-select ref-book="rbHospitalBedProfile" ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused></rb-select>';
                                    break;
                                case 'Person':
                                    inner_template = '<wm-person-select ng-model="{0}.value"\
                                        id="[[{0}.type.id]]" al-item-focused></wm-person-select>';
                                    break;
                                case 'Organisation':
                                    inner_template =
                                        '<ui-select ng-model="{0}.value" theme="select2" class="form-control"\
                                                autocomplete="off" ref-book="Organisation" id="[[{0}.type.id]]" al-item-focused>\
                                            <ui-select-match placeholder="не выбрано">[[ $select.selected.full_name ]]</ui-select-match>\
                                            <ui-select-choices repeat="item in $refBook.objects | filter: $select.search | limitTo: 50">\
                                                <span ng-bind-html="item.full_name | highlight: $select.search"></span>\
                                            </ui-select-choices>\
                                        </ui-select>';
                                    break;
                                case 'MKB':
                                    inner_template = '<ui-select ext-select-mkb ng-model="{0}.value" id="[[{0}.type.id]]" al-item-focused></ui-select>';
                                    break;
                                case 'OrgStructure': // Без фильтров
                                    inner_template =
                                        '<wm-custom-dropdown>\
                                            <wm-org-structure-tree ng-model="{0}.value" id="[[{0}.type.id]]" al-item-focused></wm-org-structure-tree>\
                                        </wm-custom-dropdown>';
                                    break;
                                case 'ReferenceRb':
                                    var domain = property.type.domain.split(';'),
                                        rbTable = domain[0],
                                        rb_codes = domain[1] ? (domain[1].split(',').map(function (code) {
                                            return "'{0}'".format(code.trim());
                                        }).filter(function (code) {
                                            return code !== "''";
                                        })) : [],
                                        extra_filter = rb_codes.length ? 'attribute:\'code\':[{0}]'.format(rb_codes.join(',')) : '';
                                    inner_template = '<rb-select ref-book="{1}" ng-model="{0}.value" extra-filter="{2}"\
                                        allow-clear="true" id="[[{0}.type.id]]" al-item-focused no-undefined-value></rb-select>'
                                            .format('{0}', rbTable, extra_filter);
                                    break;
                                case 'Diagnosis':
                                    inner_template = ('<wm-diagnosis model="{0}.value" action="action" params="{1}" ' +
                                        'can-add-new="true" can-delete="true" can-edit="true" list-mode="{2}">' +
                                        '</wm-diagnosis>').format('{0}', property_value_domain_obj, property.type.vector);
                                    break;
                                case 'URL':
                                    inner_template = scope.action.is_new() || !property.value ?
                                        '<span></span>' :
                                        '<a ng-href="[[{0}.value]]" target="_blank" title="Открыть ссылку в новой вкладке"\
                                            style="font-size:larger; margin-left: 10px; margin-top: 5px;"\
                                            id="[[{0}.type.id]]">[[ {0}.type.description || {0}.value ]]</a>';
                                    break;
                                default:
                                    inner_template = '<span ng-bind="{0}.value" id="[[{0}.type.id]]"></span>';
                            }
                        }

                        var property_name = tag.title || property.type.name;
                        var template;
                        if (context === undefined) {
                            if (scope.action.readonly) {
                                template = '<div><label>{0}:</label> {1}</div>'.format(property_name, inner_template.format(property_code))
                            } else {
                                template =
                                    '<div class="form-group">\
                                    <wm-checkbox select-all="sas" \
                                                    ng-hide="{3}" \
                                                    initially-checked="{3}" \
                                                    on-checked="layout_tools.onCheckboxSelected({2})"\
                                                    key="{2}">{0}</wm-checkbox>\
                                    <div ng-show="sas.selected({2})">{1}</div></div>'.format(
                                        property_name,
                                        inner_template.format(property_code),
                                        property.type.id,
                                        property.type.mandatory);
                            }
                        } else {
                            if (context.tag.tagName === 'table') {
                                template = '<tr>\
                                    <td><label>{0}</label></td>\
                                    <td class="text-center"><input type="checkbox" ng-model="{1}.is_assigned" ng-if="{2}" ng-disabled={3}></td>\
                                    <td>{4}</td>\
                                    <td class="text-center">{5}</td>\
                                </tr>'.format(
                                    property_name,
                                    property_code,
                                    property_is_assignable,
                                    scope.action.readonly || property.type.mandatory || property.has_pricelist_service,
                                    inner_template.format(property_code),
                                    property.type.norm ? property.type.norm : ''
                                );
                            } else if (context.tag.tagName === 'vgroup') {
                                template = '<div class="row">\
                                    <div class="col-sm-3">\
                                        <label><input type="checkbox" ng-model="{1}.is_assigned">{0}</label>\
                                    </div>\
                                    <div class="col-sm-9"><div ng-show="sas.selected({3})">{2}</div></div>\
                                </div>'.format(
                                    property_name,
                                    property_code,
                                    inner_template.format(property_code),
                                    property.type.id
                                );
                            }
                        }

                        if (!property || !property.value) {
                            sas.select(tag.id, false);
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
                        return '<div class="row">{0}</div><hr>'.format(inner_template);

                    case 'table':
                        return '\
                            <table class="table table-hover">\
                                <thead>\
                                    <th width="35%"></th>\
                                    <th width="15%" class="text-center">Назначено</th>\
                                    <th width="30%">Значение</th>\
                                    <th width="20%" class="text-center">Норма</th>\
                                </thead>\
                                {0}\
                            </table>\
                        '.format(tag.children.map(function (child) {
                            if (child.tagName !== 'ap') {throw '"table" tags only support "ap" children';}
                            return build(child, {tag: tag});
                        }).join(''));

                    case 'bak_lab_view':
                        return '<bak-lab-view model="action.get_baklab_info()"></bak-lab-view>';

                    case 'prescriptions':
                        return scope.action.prescriptions ?
                            '<legend class="vmargin10">Назначения медицинских препаратов</legend>\
                             <medication-prescriptions model="action.prescriptions" action="action"/>' :
                            '';

                    case 'root':
                        inner_template = tag.children.map(function (child) {
                            return '<div class="row"><div class="col-md-12">{0}</div></div>'.format(build(child))
                        }).join('');
                        return '<div class="row marginal"><div class="col-md-12">{0}</div></div>'.format(inner_template);

                    default:
                        return '<div>[[ tag | json ]]</div>';
                }
            }

            var sas = scope.sas = new SelectAll([]);
            var sas_vgroup = scope.sas_vgroup = new SelectAll([]);

            scope.$watchCollection('action.properties', function (properties, old) {
                //if (angular.equals(properties, old)) return;
                properties = properties || [];
                old = old || [];
                if (angular.equals(properties, old)) return;
                sas.setSource(_.map(properties, function (item) {return item.type.id}));
                sas.selectNone();

                var map_old = {};
                _.each(old, function (prop) { map_old[prop.type.id] = prop });
                _.each(properties, function (prop) {
                    var id = prop.type.id,
                        old_prop = map_old[id];
                    // Здесь нужна будет точная подгонка под фантазии Опарина
                    if (prop.value || (!_.isUndefined(old_prop) && !angular.equals(old_prop.value, prop.value))) {
                        sas.select(id);
                    }
                })
            });

            function rebuild_layout (layout) {
                v_groups_count = 0;
                var template = build(layout);
                sas_vgroup.setSource(aux.range(v_groups_count));
                sas_vgroup.selectAll();
                var replace = $(template);
                $(current_element).replaceWith(replace);
                current_element = replace;
                $compile(replace)(scope);
                return layout;
            }

            scope.$watchCollection('action.layout', rebuild_layout);

            scope.$watch('action.readonly', function (n, o) {
                if (!angular.equals(n, o)) {
                    rebuild_layout(scope.action.layout)
                }
            });
        }
    }
}])
.directive('alItemFocused', [function () {
    return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
            var focusActionLayoutItem = function (id) {
                document.getElementById(id).focus();
            };
            scope.$on('actionLayoutItemFocused', function (event, args) {
                if (String(args.apt_id) === elem.attr('id')) {
                    var phase = scope.$root.$$phase;
                    if (phase == '$apply' || phase == '$digest') {
                        focusActionLayoutItem(elem.attr('id'));
                    } else {
                        scope.$apply(focusActionLayoutItem(elem.attr('id')));
                    }
                }
            });
        }
    }
}])
;
