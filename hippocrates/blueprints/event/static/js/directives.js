'use strict';

angular.module('WebMis20')
.directive('wmEventServiceListHeader', [function () {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {

        },
        template:
'<th></th>\
<th>Код</th>\
<th>Услуга</th>\
<th class="nowrap">Документ</th>\
<th class="nowrap" ng-show="formstate.is_paid()">Цена (руб.)</th>\
<th>Количество</th>\
<th class="nowrap" ng-show="formstate.is_paid()">Сумма (руб.)</th>\
<th></th>'
    };
}])
.directive('wmEventServiceGroup', ['WMEventFormState', 'WMEventServices', 'ActionTypeTreeModal', 'CurrentUser',
function(WMEventFormState, WMEventServices, ActionTypeTreeModal, CurrentUser) {
    return {
        restrict: 'A',
        scope: {
            serviceGroupData: '=',
            idx: '=',
            expanded: '=',
            editInvoiceMode: '='
        },
        link: function (scope, elm, attrs) {
            scope.formstate = WMEventFormState;
            scope.eventServices = WMEventServices;

            scope.$watch('editInvoiceMode', function (newVal) {
                scope.expanded = newVal;
            });

            //scope.coord_all = function (off) {
            //    scope.service.coord_all = !Boolean(off);
            //};
            //scope.open_assignments = function () {
            //    var assigned = scope.service.all_assigned,
            //        ped = scope.service.all_planned_end_date;
            //
            //    if (assigned === false || ped === false) {
            //        if (!confirm(
            //                'Осмотры данной группы имеют разные наборы назначаемых исследований или ' +
            //                'разные даты проведения. Выбрать новые параметры исследований ' +
            //                'для всех осмотров группы?')) {
            //            return
            //        }
            //        assigned = scope.service.assignable.map(function (asgn_data) {
            //            return asgn_data[0];
            //        });
            //        ped = null;
            //    }
            //    var model = {
            //        assignable: scope.service.assignable,
            //        assigned: assigned,
            //        planned_end_date: ped,
            //        ped_disabled: scope.service.actions.every(function (act) {
            //            return act.action_id;
            //        })
            //    };
            //    ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
            //        scope.service.actions.forEach(function (act) {
            //            if (!act.is_closed()) {
            //                act.assigned = model.assigned;
            //            }
            //            if (!act.action_id) {
            //                act.planned_end_date = model.planned_end_date;
            //            }
            //        });
            //    });
            //};
            //
            //scope.btn_coordinate_visible = function () {
            //    return !scope.service.fully_coord && !scope.service.all_actions_closed && !scope.event.ro;
            //};
            //scope.btn_cancel_coordinate_visible = function () {
            //    return scope.service.fully_coord && !scope.service.all_actions_closed && !scope.event.ro;
            //};
            //scope.btn_delete_visible = function () {
            //    var s = scope.service;
            //    return !(
            //        s.fully_paid || s.partially_paid || s.fully_coord || s.partially_coord ||
            //        scope.service.all_actions_closed || scope.event.ro
            //    );
            //};
            //scope.lab_components_disabled = function () {
            //    return (scope.service.fully_paid || scope.service.fully_coord ||
            //        scope.service.all_actions_closed || scope.event.ro);
            //};
        },
        template:
'<td class="sg-expander" ng-click="expanded = !expanded"><span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span></td>\
<td ng-bind="serviceGroupData.service_code"></td>\
<td>\
    [[serviceGroupData.service_name]]\
    <!-- <a href="javascript:;" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
        ng-disabled="lab_components_disabled()">Выбрать назначаемые исследования</a> -->\
</td>\
<td ng-bind="serviceGroupData.at_name"></td>\
<td ng-bind="serviceGroupData.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td ng-bind="serviceGroupData.total_amount" class="text-right"></td>\
<td ng-bind="serviceGroupData.total_sum" class="text-right" ng-show="formstate.is_paid()"></td>\
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
            service: '=',
            idx: '=',
            serviceGroup: '=',
            editMode: '=',
            editInvoiceMode: '=',
            newInvoice: '=',
            onChangeCallback: '&onChange'
        },
        link: function(scope, elm, attrs) {
            scope.formstate = WMEventFormState;
            scope.eventServices = WMEventServices;
            scope.ActionStatus = RefBookService.get('ActionStatus');

            scope.onAmountChanged = function () {
                scope.service.service.sum = scope.service.service.price * scope.service.service.amount;
                scope.onChangeCallback();
            };
            scope.removeService = function () {
                if (scope.service.service.id) {
                    if (!confirm('Вы действительно хотите удалить выбранную услугу?')) return;
                    // todo
                } else {
                    scope.serviceGroup.sg_list.splice(scope.idx, 1);
                    // todo - удалить группу, если услуга одна
                }
            };
            scope.inNewInvoice = false;
            scope.isInNewInvoice = function () {
                return scope.inNewInvoice;
            };
            scope.addServiceToInvoice = function () {
                scope.newInvoice.push(scope.service);
                scope.inNewInvoice = true;
            };
            scope.removeServiceFromInvoice = function () {
                var idx = _.indexOf(scope.newInvoice, scope.service);
                scope.newInvoice.splice(idx, 1);
                scope.inNewInvoice = false;
            };
            scope.$watch('editInvoiceMode', function (newVal) {
                if (newVal) scope.inNewInvoice = false;
            });

            //scope.open_assignments = function () {
            //    var model = {
            //        assignable: scope.service.assignable,
            //        assigned: scope.action.assigned,
            //        planned_end_date: scope.action.planned_end_date,
            //        ped_disabled: Boolean(scope.action.action_id)
            //    };
            //    ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
            //        scope.action.assigned = model.assigned;
            //        scope.action.planned_end_date = model.planned_end_date;
            //    });
            //};
            //scope.get_info_text = function () {
            //    function get_action_status_text(status_code) {
            //        var status_item = scope.ActionStatus.objects.filter(function (status) {
            //            return status.id === status_code;
            //        })[0];
            //        return status_item ? status_item.name : '';
            //    }
            //    var msg = [
            //        'Идентификатор: ' + scope.action.action_id,
            //        'Дата начала: ' + (scope.action.beg_date ? $filter('asDateTime')(scope.action.beg_date) : 'отсутствует'),
            //        'Дата окончания: ' + (scope.action.end_date ? $filter('asDateTime')(scope.action.end_date) : 'отсутствует'),
            //        'Статус: ' + get_action_status_text(scope.action.status),
            //        scope.formstate.is_dms() ?
            //            'Согласовано: ' + (
            //                scope.action.is_coordinated() ?
            //                    '' + $filter('asDateTime')(scope.action.coord_date) + ', ' + (
            //                        scope.action.coord_person.name ? scope.action.coord_person.name : '') :
            //                    'нет') :
            //            ''
            //    ];
            //    return msg.join('; ');
            //};
            //scope.get_ps = function () {
            //    return scope.service.print_services[scope.idx];
            //};
            //scope.get_ps_resolve = function () {
            //    return {
            //        action_id: scope.action.action_id
            //    };
            //};
            //
            scope.amountDisabled = function () {
                return !scope.editMode;
            };
            scope.btnRemoveVisible = function () {
                return scope.editMode;
                return !(scope.action.is_paid_for() || scope.action.is_coordinated() ||
                    scope.action.is_closed() || scope.event.ro);
            };
            scope.btnAddToInvoiceVisible = function () {
                return scope.editInvoiceMode && !scope.service.service.in_invoice && !scope.isInNewInvoice();
            };
            scope.btnRemoveFromInvoiceVisible = function () {
                return scope.editInvoiceMode && !scope.service.service.in_invoice && scope.isInNewInvoice();
            };
            //scope.lab_components_disabled = function () {
            //    return scope.action.account || scope.action.is_coordinated() || scope.action.is_closed() || scope.event.ro;
            //};
        },
        template:
'<td>\
    <i class="fa fa-square-o cursor-pointer" ng-if="btnAddToInvoiceVisible()" ng-click="addServiceToInvoice()"\
        style="font-size: larger"></i>\
    <i class="fa fa-check-square-o cursor-pointer" ng-if="btnRemoveFromInvoiceVisible()" ng-click="removeServiceFromInvoice()"\
        style="font-size: larger"></i>\
</td>\
<td ng-bind="service.service.service_code"></td>\
<td>\
    [[service.service.service_name]]\
    <!-- <a  href="javascript:;" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
        ng-disabled="lab_components_disabled()">Выбрать назначаемые исследования</a> -->\
</td>\
<td ng-bind="service.action.at_name"></td>\
<td ng-bind="service.service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm"\
           ng-disabled="amountDisabled()" ng-model="service.service.amount" ng-change="onAmountChanged()"\
           valid-number minval="1"/>\
</td>\
<td ng-bind="service.service.sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<!-- <td class="text-center" ng-show="formstate.is_paid()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_paid_for(), \'glyphicon-remove\':!action.is_paid_for()}"></span>\
</td> -->\
<td nowrap class="text-right">\
    <!-- <span class="glyphicon glyphicon-info-sign" ng-if="action.action_id"\
        popover-trigger="mouseenter" popover-popup-delay=\'1000\' popover-placement="left" popover="[[get_info_text()]]"></span>\
    <ui-print-button ps="get_ps()" resolve="get_ps_resolve()" lazy-load-context="[[service.print_context]]"\
        ng-if="action.action_id"></ui-print-button> -->\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг" ng-show="btnRemoveVisible()"\
            ng-click="removeService()"><span class="fa fa-trash"></span>\
    </button>\
</td>'
    };
}])
.directive('wmActionList', [
    '$window', '$http', 'LabDynamicsModal', 'ActionTypeTreeModal', 'MessageBox', 'WMEventServices', 'WMWindowSync', 'CurrentUser', 'WMConfig',
function ($window, $http, LabDynamicsModal, ActionTypeTreeModal, MessageBox, WMEventServices, WMWindowSync, CurrentUser, WMConfig) {
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
                        event_type_id: scope.event.info.event_type.id
//                        contract_id: scope.event.info.contract.id
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
            scope.open_lab_res_dynamics = function(action){
                LabDynamicsModal.openLabDynamicsModal(scope.event, action);
            }
            scope.reset_sorting();
            scope.reload();
        },
        template:
'<table class="table table-condensed table-hover table-clickable novmargin">\
    <thead wm-sortable-header>\
    <tr>\
        <th width="45%" wm-sortable-column="at_name" on-change-order="sort_by_column(params)">Тип действия</th>\
        <th width="10%" wm-sortable-column="status_code" on-change-order="sort_by_column(params)">Состояние</th>\
        <th width="10%" wm-sortable-column="beg_date" on-change-order="sort_by_column(params)">Начало</th>\
        <th width="10%" wm-sortable-column="end_date" on-change-order="sort_by_column(params)">Конец</th>\
        <th width="20%" wm-sortable-column="person_name" on-change-order="sort_by_column(params)">Исполнитель</th>\
        <th width="5%"></th>\
        <th width="5%" ng-if="actionTypeGroup == \'lab\'"></th>\
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
        <td ng-if="actionTypeGroup == \'lab\'">\
            <button type="button" class="btn btn-sm btn-info" title="Динамика"\
                    ng-click="open_lab_res_dynamics(action)"><span class="glyphicon glyphicon-stats"></span>\
            </button>\
        </td>\
    </tr>\
    </tbody>\
    <tfoot>\
    <tr>\
        <td colspan="6">\
            <hr class="novmargin">\
            <button type="button" class="btn btn-link btn-lg pull-right" ng-click="open_action_tree(actionTypeGroup)"\
                    ng-if="can_create_action()"><i class="ion ion-plus-round fa-fw"></i>Добавить</button>\
            <pagination ng-model="pager.current_page" total-items="pager.pages" items-per-page="1"\
                max-size="pager.max_size" ng-change="reload()" ng-show="pager.pages > 1" boundary-links="true"></pagination>\
        </td>\
    </tr>\
    </tfoot>\
</table>'
    }
}])
.service('LabDynamicsModal', ['$modal', '$http', function ($modal, $http) {
        return {
        openLabDynamicsModal: function (event, action) {
            var LabResDynamicsCtrl = function ($scope) {
                $scope.date_range = [moment().subtract(5, 'days').toDate(), new Date()];
                $scope.currentDate = new Date();
                $scope.dynamics = [];
                $scope.xAxisTickFormat = function(d){
                    return moment(d).format('DD.MM.YYYY');
                }
                $scope.get_dynamics_data = function() {
                    $http.get(
                        url_lab_res_dynamics, {
                            params: {
                                event_id: event.event_id,
                                action_type_id: action.type.id,
                                from_date: $scope.date_range[0],
                                to_date: $scope.date_range[1]
                            }
                        }
                    ).success(function (data) {
                        $scope.dates_list = data.result[0]
                        $scope.dynamics = data.result[1];
                    })
                    };
                $scope.$watchCollection('date_range', function (new_val, old_val) {
                            if (angular.equals(new_val, old_val)) return;
                            if(new_val[0] && new_val[1]){
                                $scope.get_dynamics_data();
                            }
                        });
                $scope.get_dynamics_data();
            };
            var instance = $modal.open({
                templateUrl: 'modal-lab-res-dynamics.html',
                controller: LabResDynamicsCtrl,
                size: 'lg'
            });
            return instance.result.then(function() {

            });
        }
   }
}])
;