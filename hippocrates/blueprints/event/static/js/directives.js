'use strict';

angular.module('WebMis20')
.directive('wmEventServiceGroup', ['WMEventFormState', 'WMEventServices', 'ActionTypeTreeModal', 'CurrentUser',
function(WMEventFormState, WMEventServices, ActionTypeTreeModal, CurrentUser) {
    return {
        restrict: 'A',
        scope: {
            service: '=model',
            event: '=',
            idx: '=',
            expanded: '='
        },
        controller: function ($scope) {
            $scope.get_min_amount = function () {
                var m = 0;
                $scope.service.actions.forEach(function (act) {
                    if (act.action_id || act.account || act.is_coordinated()) {
                        m += act.amount;
                    }
                });
                return m || 1;
            };
            $scope.get_max_amount = function () {
                // max # of actions = 100 + sum amounts for each action
                var m = 100;
                $scope.service.actions.forEach(function (act) {
                    m += act.amount - 1;
                });
                return m;
            };
        },
        link: function (scope, elm, attrs) {
            scope.formstate = WMEventFormState;
            scope.eventServices = WMEventServices;

            scope.coord_all = function (off) {
                scope.service.coord_all = !Boolean(off);
            };
            scope.open_assignments = function () {
                var assigned = scope.service.all_assigned,
                    ped = scope.service.all_planned_end_date;

                if (assigned === false || ped === false) {
                    if (!confirm(
                            'Осмотры данной группы имеют разные наборы назначаемых исследований или ' +
                            'разные даты проведения. Выбрать новые параметры исследований ' +
                            'для всех осмотров группы?')) {
                        return
                    }
                    assigned = scope.service.assignable.map(function (asgn_data) {
                        return asgn_data[0];
                    });
                    ped = null;
                }
                var model = {
                    assignable: scope.service.assignable,
                    assigned: assigned,
                    planned_end_date: ped,
                    ped_disabled: scope.service.actions.every(function (act) {
                        return act.action_id;
                    })
                };
                ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
                    scope.service.actions.forEach(function (act) {
                        if (!act.is_closed()) {
                            act.assigned = model.assigned;
                        }
                        if (!act.action_id) {
                            act.planned_end_date = model.planned_end_date;
                        }
                    });
                });
            };

            scope.amount_disabled = function () {
                return scope.service.fully_paid || scope.service.fully_coord || scope.event.ro;
            };
            scope.account_disabled = function () {
                return !CurrentUser.current_role_in('admin', 'clinicRegistrator');
            };
            scope.btn_coordinate_visible = function () {
                return !scope.service.fully_coord && !scope.service.all_actions_closed && !scope.event.ro;
            };
            scope.btn_cancel_coordinate_visible = function () {
                return scope.service.fully_coord && !scope.service.all_actions_closed && !scope.event.ro;
            };
            scope.btn_delete_visible = function () {
                var s = scope.service;
                return !(
                    s.fully_paid || s.partially_paid || s.fully_coord || s.partially_coord ||
                    scope.service.all_actions_closed || scope.event.ro
                );
            };
            scope.lab_components_disabled = function () {
                return (scope.service.fully_paid || scope.service.fully_coord ||
                    scope.service.all_actions_closed || scope.event.ro);
            };
        },
        template:
'<td class="sg-expander" ng-click="expanded = !expanded"><span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span></td>\
<td ng-bind="service.code"></td>\
<td>\
    [[service.name]]\
    <a href="javascript:;" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
        ng-disabled="lab_components_disabled()">Выбрать назначаемые исследования</a>\
</td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm"\
           ng-disabled="amount_disabled()" ng-model="service.total_amount"\
           valid-number min-val="get_min_amount()" max-val="get_max_amount()"\
           wm-debounce />\
</td>\
<td ng-bind="service.total_sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать для оплаты" ng-model="service.account_all" ng-disabled="account_disabled()">\
</td>\
<td ng-bind="service.paid_count" class="text-center" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_dms()">\
    <button type="button" class="btn btn-sm btn-default" title="Согласовать"\
            ng-show="btn_coordinate_visible()"\
            ng-click="coord_all()"><span class="glyphicon glyphicon-check"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-default" title="Отменить согласование"\
            ng-show="btn_cancel_coordinate_visible()"\
            ng-click="coord_all(\'off\')"><span class="glyphicon glyphicon-remove"></span>\
    </button>\
</td>\
<td ng-bind="service.coord_count" class="text-center" ng-show="formstate.is_dms()"></td>\
<td nowrap class="text-right">\
    <button type="button" class="btn btn-sm btn-danger" title="Удалить услуги"\
            ng-show="btn_delete_visible()"\
            ng-click="eventServices.remove_service(event, idx)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
    };
}])
.directive('wmEventServiceRecord', [
    'WMEventFormState', 'WMEventServices', 'ActionTypeTreeModal', '$filter', 'RefBookService', 'CurrentUser',
function(WMEventFormState, WMEventServices, ActionTypeTreeModal, $filter, RefBookService, CurrentUser) {
    return {
        restrict: 'A',
        scope: {
            action: '=',
            service: '=',
            event: '=',
            idx: '='
        },
        link: function(scope, elm, attrs) {
            scope.formstate = WMEventFormState;
            scope.eventServices = WMEventServices;
            scope.ActionStatus = RefBookService.get('ActionStatus');

            scope.change_action_choice_for_payment = function() {
                if (scope.action.account) {
                    scope.service.payments.add_charge(scope.action);
                } else {
                    scope.service.payments.remove_charge(scope.action);
                }
            };
            scope.open_assignments = function () {
                var model = {
                    assignable: scope.service.assignable,
                    assigned: scope.action.assigned,
                    planned_end_date: scope.action.planned_end_date,
                    ped_disabled: Boolean(scope.action.action_id)
                };
                ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
                    scope.action.assigned = model.assigned;
                    scope.action.planned_end_date = model.planned_end_date;
                });
            };
            scope.get_info_text = function () {
                function get_action_status_text(status_code) {
                    var status_item = scope.ActionStatus.objects.filter(function (status) {
                        return status.id === status_code;
                    })[0];
                    return status_item ? status_item.name : '';
                }
                var msg = [
                    'Идентификатор: ' + scope.action.action_id,
                    'Дата начала: ' + (scope.action.beg_date ? $filter('asDateTime')(scope.action.beg_date) : 'отсутствует'),
                    'Дата окончания: ' + (scope.action.end_date ? $filter('asDateTime')(scope.action.end_date) : 'отсутствует'),
                    'Статус: ' + get_action_status_text(scope.action.status),
                    scope.formstate.is_dms() ?
                        'Согласовано: ' + (
                            scope.action.is_coordinated() ?
                                '' + $filter('asDateTime')(scope.action.coord_date) + ', ' + (
                                    scope.action.coord_person.name ? scope.action.coord_person.name : '') :
                                'нет') :
                        ''
                ];
                return msg.join('; ');
            };
            scope.get_ps = function () {
                return scope.service.print_services[scope.idx];
            };
            scope.get_ps_resolve = function () {
                return {
                    action_id: scope.action.action_id
                };
            };

            scope.amount_disabled = function () {
                return scope.action.account || scope.action.is_coordinated() || scope.event.ro;
            };
            scope.account_disabled = function () {
                return !CurrentUser.current_role_in('admin', 'clinicRegistrator');
            };
            scope.btn_coordinate_visible = function () {
                return !scope.action.is_coordinated() && !scope.action.is_closed() && !scope.event.ro;
            };
            scope.btn_cancel_coordinate_visible = function () {
                return scope.action.is_coordinated() && !scope.action.is_closed() && !scope.event.ro;
            };
            scope.btn_delete_visible = function () {
                return !(scope.action.is_paid_for() || scope.action.is_coordinated() ||
                    scope.action.is_closed() || scope.event.ro);
            };
            scope.lab_components_disabled = function () {
                return scope.action.account || scope.action.is_coordinated() || scope.action.is_closed() || scope.event.ro;
            };
        },
        template:
'<td></td>\
<td ng-bind="service.code"></td>\
<td>\
    [[service.name]]\
    <a  href="javascript:;" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
        ng-disabled="lab_components_disabled()">Выбрать назначаемые исследования</a>\
</td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm"\
           ng-disabled="amount_disabled(action)" ng-model="action.amount"\
           valid-number minval="1"/>\
</td>\
<td ng-bind="action.sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать услугу для оплаты" ng-model="action.account"\
        ng-change="change_action_choice_for_payment()" ng-disabled="account_disabled()">\
</td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_paid_for(), \'glyphicon-remove\':!action.is_paid_for()}"></span>\
</td>\
<td class="text-center" ng-show="formstate.is_dms()">\
    <button type="button" class="btn btn-sm btn-default" title="Согласовать"\
            ng-show="btn_coordinate_visible()"\
            ng-click="eventServices.coordinate(action)"><span class="glyphicon glyphicon-check"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-default" title="Отменить согласование"\
            ng-show="btn_cancel_coordinate_visible()"\
            ng-click="eventServices.coordinate(action, \'off\')"><span class="glyphicon glyphicon-remove"></span>\
    </button>\
</td>\
<td class="text-center" ng-show="formstate.is_dms()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_coordinated(), \'glyphicon-remove\':!action.is_coordinated()}"></span>\
</td>\
<td nowrap class="text-right">\
    <span class="glyphicon glyphicon-info-sign" ng-if="action.action_id"\
        popover-trigger="mouseenter" popover-popup-delay=\'1000\' popover-placement="left" popover="[[get_info_text()]]"></span>\
    <ui-print-button ps="get_ps()" resolve="get_ps_resolve()" lazy-load-context="[[service.print_context]]"\
        ng-if="action.action_id"></ui-print-button>\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="eventServices.remove_action(event, action, service)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
    };
}])
.directive('wmEventServiceListHeader', ['CurrentUser', function (CurrentUser) {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            scope.all_accounted = false;
            scope.$watch(function () {
                return scope.event.services.map(function (sg) {
                    return sg.account_all;
                }).every(Boolean);
            }, function (n, o) {
                scope.all_accounted = n;
            });
            scope.account_all = function () {
                scope.event.services.forEach(function (sg) {
                    sg.account_all = scope.all_accounted;
                });
            };
            scope.account_disabled = function () {
                return !CurrentUser.current_role_in('admin', 'clinicRegistrator');
            };
        },
        template:
'<th></th>\
<th>Код</th>\
<th>Услуга</th>\
<th class="nowrap">Тип действия</th>\
<th class="nowrap" ng-show="formstate.is_paid()">Цена (руб.)</th>\
<th>Количество</th>\
<th class="nowrap" ng-show="formstate.is_paid()">Сумма к оплате (руб.)</th>\
<th class="nowrap" ng-show="formstate.is_paid()">\
    <div class="inline-checkbox">\
        <input type="checkbox" ng-model="all_accounted" ng-change="account_all()"\
            ng-disabled="account_disabled()">Считать\
    </div>\
</th>\
<th ng-show="formstate.is_paid()">Оплачено</th>\
<th ng-show="formstate.is_dms()">Согласовать</th>\
<th ng-show="formstate.is_dms()">Согласовано</th>\
<th></th>'
    };
}])
.directive('wmActionList', [
    '$window', '$http', 'ActionTypeTreeModal', 'MessageBox', 'WMEventServices', 'WMWindowSync', 'CurrentUser', 'WMConfig',
function ($window, $http, ActionTypeTreeModal, MessageBox, WMEventServices, WMWindowSync, CurrentUser, WMConfig) {
    return {
        restrict: 'E',
        scope: {
            event: '=',
            actionTypeGroup: '@'
        },
        link: function (scope, element, attrs) {
            var at_class = {
                'medical_documents': 0,
                'diagnostics': 1,
                'lab': 1,
                'treatments': 2
            };
            scope.actions = [];
            scope.pager = {
                current_page: 1,
                per_page: 15,
                max_size: 10,
                pages: 1
            };

            scope.reload = function () {
                var url = '{0}{1}/{2}/{3}/{4}/{5}/{6}/'.format(
                    WMConfig.url.api_event_actions,
                    scope.event.event_id,
                    scope.actionTypeGroup,
                    scope.pager.current_page,
                    scope.pager.per_page,
                    scope.current_sorting.column_name,
                    scope.current_sorting.order.toLowerCase()
                );
                $http.get(url).success(function (data) {
                    scope.actions = data.result.items;
                    scope.pager.pages = data.result.pages;
                });
            };
            scope.reset_sorting = function () {
                scope.current_sorting = {
                    order: 'DESC',
                    column_name: 'beg_date'
                };
                var i,
                    columns = scope.wmSortableHeaderCtrl.sort_cols;
                for (i = 0; i < columns.length; ++i) {
                    if (columns[i].column_name === 'beg_date') {
                        columns[i].order = 'DESC';
                    } else {
                        columns[i].order = undefined;
                    }
                }
            };
            scope.sort_by_column = function (params) {
                scope.current_sorting = params;
                scope.reload();
            };

            scope.can_delete_action = function (action) {
                return CurrentUser.current_role_in('admin') || (action.status.code !== 'finished' && action.can_delete);
            };
            scope.can_create_action = function () {
                return scope.event.can_create_actions[at_class[scope.actionTypeGroup]];
            };
            scope.open_action = function (action_id) {
                var url = url_for_schedule_html_action + '?action_id=' + action_id;
                WMWindowSync.openTab(url, scope.update_event);
            };
            scope.open_action_tree = function (at_class) {
                ActionTypeTreeModal.open(
                    scope.event.event_id,
                    scope.event.info.client.info,
                    {
                        at_group: at_class,
                        event_type_id: scope.event.info.event_type.id,
                        contract_id: scope.event.info.contract.id
                    },
                    function afterActionCreate() {
                        scope.pager.current_page = 1;
                        scope.update_event();
                    }
                );
            };
            scope.update_event = function () {
                scope.event.reload().then(function () {
                    scope.$root.$broadcast('event_loaded');
                });
                scope.reload();
            };
            scope.delete_action = function (action) {
                MessageBox.question(
                    'Удаление записи',
                    'Вы уверены, что хотите удалить "{0}"?'.format(safe_traverse(action, ['name']))
                ).then(function () {
                    WMEventServices.delete_action(
                        scope.event, action
                    ).then(function () {
                        scope.update_event();
                    }, function () {
                        alert('Ошибка удаления действия. Свяжитесь с администратором.');
                    });
                });
            };

            scope.reset_sorting();
            scope.reload();
        },
        template:
'<table class="table table-condensed table-hover table-clickable">\
    <thead wm-sortable-header>\
    <tr>\
        <th width="45%" wm-sortable-column="at_name" on-change-order="sort_by_column(params)">Тип действия</th>\
        <th width="10%" wm-sortable-column="status_code" on-change-order="sort_by_column(params)">Состояние</th>\
        <th width="10%" wm-sortable-column="beg_date" on-change-order="sort_by_column(params)">Начало</th>\
        <th width="10%" wm-sortable-column="end_date" on-change-order="sort_by_column(params)">Конец</th>\
        <th width="20%" wm-sortable-column="person_name" on-change-order="sort_by_column(params)">Исполнитель</th>\
        <th width="5%"></th>\
    </tr>\
    </thead>\
    <tbody>\
    <tr ng-repeat="action in actions" ng-class="{\'success\': action.status.code == \'finished\'}">\
        <td ng-click="open_action(action.id)">[[ action.name ]]</td>\
        <td ng-click="open_action(action.id)">[[action.status.name]]</td>\
        <td ng-click="open_action(action.id)">[[ action.begDate | asDate ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.endDate | asDateTime ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.person_text ]]</td>\
        <td>\
            <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-show="can_delete_action(action)"\
                    ng-click="delete_action(action)"><span class="glyphicon glyphicon-trash"></span>\
            </button>\
        </td>\
    </tr>\
    </tbody>\
    <tfoot>\
    <tr>\
        <td colspan="6">\
            <button type="button" class="btn btn-primary pull-right tmargin20" ng-click="open_action_tree(actionTypeGroup)"\
                    ng-if="can_create_action()">Создать</button>\
            <pagination ng-model="pager.current_page" total-items="pager.pages" items-per-page="1"\
                max-size="pager.max_size" ng-change="reload()" ng-show="pager.pages > 1" boundary-links="true"></pagination>\
        </td>\
    </tr>\
    </tfoot>\
</table>'
    }
}])
;