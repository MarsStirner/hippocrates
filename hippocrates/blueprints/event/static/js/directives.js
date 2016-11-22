'use strict';

angular.module('WebMis20')
.directive('wmEventServiceListHeader', ['WMEventFormState', function (WMEventFormState) {
    return {
        restrict: 'A',
        replace: true,
        scope: {
            editInvoiceMode: '='
        },
        link: function (scope, element, attrs) {
            scope.formstate = WMEventFormState;
            scope.inEditInvoiceMode = function () {
                return scope.editInvoiceMode;
            };
        },
        template:
'<tr>\
    <th ng-if="inEditInvoiceMode()"></th>\
    <th></th>\
    <th>Код</th>\
    <th>Услуга</th>\
    <th class="nowrap">Наименование</th>\
    <th class="nowrap" ng-show="formstate.is_paid()">Цена (руб.)</th>\
    <th ng-show="formstate.is_paid()">Скидка</th>\
    <th>Количество</th>\
    <th class="nowrap" ng-show="formstate.is_paid()">Сумма (руб.)</th>\
    <th></th>\
</tr>'
    };
}])
.directive('wmEventServiceRecord', ['WMEventFormState', 'AccountingService', 'ActionTypeTreeModal',
        function(WMEventFormState, AccountingService, ActionTypeTreeModal) {
    return {
        restrict: 'A',
        replace: true,
        scope: {
            service: '=',
            event: '=',
            editMode: '=',
            editInvoiceMode: '=',
            newInvoice: '='
        },
        link: function(scope, elm, attrs) {
            scope.formstate = WMEventFormState;

            scope.getLevelMarkClass = function () {
                if (scope.service.ui_attrs.is_expandable) {
                    return scope.isExpanded() ? 'chevron-down' : 'chevron-right';
                } else {
                    return 'minus';
                }
            };
            scope.getLevelIndentStyle = function () {
                return {
                    'margin-left': '{0}px'.format(10 * scope.service.ui_attrs.level)
                }
            };
            var traverseToggleVisible = function (service, state) {
                service.ui_attrs.visible = state;
                if (service.ui_attrs.is_expandable) {
                    angular.forEach(service.subservice_list, function (sub_service) {
                        traverseToggleVisible(sub_service, service.ui_attrs.visible && service.ui_attrs.expanded);
                    });
                }
            };
            scope.toggleExpanded = function () {
                scope.service.ui_attrs.expanded = !scope.service.ui_attrs.expanded;
                angular.forEach(scope.service.subservice_list, function(sub_service) {
                    traverseToggleVisible(sub_service, scope.service.ui_attrs.expanded)
                });
            };
            scope.isExpanded = function () {
                return scope.service.ui_attrs.expanded;
            };
            scope.isVisible = function () {
                return scope.service.ui_attrs.visible;
            };
            scope.getRowClass = function () {
                if (scope.service.ui_attrs.idx % 2 !== 0) return 'bg-muted';
                else return '';
            };

            scope.isServiceLab = function () {
                return scope.service.service_kind.code === 'lab_action';
            };
            scope.openLabTestModal = function () {
                var cur_service = _.deepCopy(scope.service);
                var model = {
                    assignable: cur_service.serviced_entity.tests_data.assignable,
                    assigned: cur_service.serviced_entity.tests_data.assigned,
                    planned_end_date: aux.safe_date(cur_service.serviced_entity.tests_data.planned_end_date),
                    ped_disabled: cur_service.serviced_entity.tests_data.ped_disabled,
                    available_tissue_types: cur_service.serviced_entity.tests_data.available_tissue_types,
                    selected_tissue_type: cur_service.serviced_entity.tests_data.selected_tissue_type,
                    tissue_type_visible: cur_service.serviced_entity.tests_data.tissue_type_visible
                };
                ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
                    cur_service.serviced_entity.tests_data.assigned = model.assigned;
                    cur_service.serviced_entity.tests_data.planned_end_date = model.planned_end_date;
                    cur_service.serviced_entity.tests_data.selected_tissue_type = model.selected_tissue_type;

                    if (scope.service.ui_attrs.level === 0) {
                        AccountingService.refreshServiceSubservices(cur_service)
                            .then(function (upd_service) {
                                angular.copy(upd_service, scope.service);
                            });
                    } else {
                        var root_service = scope.event.services[scope.service.ui_attrs.root_idx],
                            saved_root_service = _.deepCopy(root_service);
                        angular.copy(cur_service, scope.service);

                        AccountingService.refreshServiceSubservices(root_service)
                            .then(function (upd_service) {
                                angular.copy(upd_service, root_service);
                            }, function () {
                                angular.copy(saved_root_service, root_service);
                            });
                    }
                });
            };

            scope.deleteService = function () {
                var idx = scope.service.ui_attrs.idx;
                if (scope.service.id) {
                    if (!confirm('Вы действительно хотите удалить выбранную услугу?')) return;
                    AccountingService.delete_service(scope.service)
                        .then(function () {
                            scope.event.services.splice(idx, 1);
                        });
                } else {
                    scope.event.services.splice(idx, 1);
                }
            };
            scope.isInNewInvoice = function () {
                return scope.service.in_new_invoice;
            };
            scope.addServiceToInvoice = function () {
                scope.newInvoice.push(scope.service);
                scope.service.in_new_invoice = true;
            };
            scope.removeServiceFromInvoice = function () {
                var idx = _.indexOf(scope.newInvoice, scope.service);
                scope.newInvoice.splice(idx, 1);
                scope.service.in_new_invoice = false;
            };
            scope.invoiceControlsVisible = function () {
                return scope.editInvoiceMode;
            };
            scope.btnAddToInvoiceVisible = function () {
                return scope.editInvoiceMode && !scope.service.in_invoice && !scope.isInNewInvoice() &&
                    scope.service.ui_attrs.level === 0;
            };
            scope.btnRemoveFromInvoiceVisible = function () {
                return scope.editInvoiceMode && !scope.service.in_invoice && scope.isInNewInvoice() &&
                    scope.service.ui_attrs.level === 0;
            };

            scope.amountDisabled = function () {
                return !scope.editMode;
            };
            scope.btnRemoveVisible = function () {
                return scope.editMode && scope.service.access.can_delete;
            };
            scope.btnLabTestModalDisabled = function () {
                return !scope.editMode || !scope.service.access.can_edit;
            };
        },
        template:
'<tr ng-show="isVisible()" ng-class="getRowClass()">\
    <td ng-if="invoiceControlsVisible()">\
        <i class="fa fa-square-o cursor-pointer" ng-show="btnAddToInvoiceVisible()" ng-click="addServiceToInvoice()"\
            style="font-size: larger"></i>\
        <i class="fa fa-check-square-o cursor-pointer" ng-show="btnRemoveFromInvoiceVisible()" ng-click="removeServiceFromInvoice()"\
            style="font-size: larger"></i>\
    </td>\
    <td class="cursor-pointer" ng-click="toggleExpanded()">\
        <span class="glyphicon glyphicon-[[getLevelMarkClass()]]" ng-style="getLevelIndentStyle()"></span>\
    </td>\
    <td ng-bind="service.service_code"></td>\
    <td>\
        <span title="[[service.service_kind.name]]">[[service.service_name]]</span>\
        <button class="btn btn-sm btn-link" ng-click="openLabTestModal()" ng-if="isServiceLab()"\
            title="Выбрать показатели исследований" ng-disabled="btnLabTestModalDisabled()"><i class="fa fa-flask"></i></button>\
    </td>\
    <td ng-bind="service.serviced_entity.name"></td>\
    <td ng-bind="service.price | moneyCut" class="text-right" ng-show="formstate.is_paid()"></td>\
    <td ng-show="formstate.is_paid()">[[ service.discount ? service.discount.description.short : ""]]</td>\
    <td>\
        <span ng-bind="service.amount"></span>\
        <!-- <input type="text" class="form-control input-sm"\
               ng-disabled="amountDisabled()" ng-model="service.amount" ng-change="onAmountChanged()"\
               valid-number minval="1" wm-debounce/> -->\
    </td>\
    <td class="text-right" ng-show="formstate.is_paid()">\
        <span ng-bind="service.sum | moneyCut"></span> <span class="glyphicon glyphicon-ok text-success" title="Оплачено" ng-show="service.is_paid"></span>\
    </td>\
    <td nowrap class="text-right">\
        <button type="button" class="btn btn-sm btn-danger" title="Удалить услугу" ng-show="btnRemoveVisible()"\
            ng-click="deleteService()"><span class="fa fa-trash"></span>\
        </button>\
    </td>\
</tr>'
    };
}])
.directive('wmActionList', [
    '$window', '$http', 'LabDynamicsModal', 'ActionTypeTreeModal', 'MessageBox', 'WMEventServices', 'WMWindowSync', 'CurrentUser',
        'WMConfig', 'PrintingService',
function ($window, $http, LabDynamicsModal, ActionTypeTreeModal, MessageBox, WMEventServices, WMWindowSync, CurrentUser, WMConfig, PrintingService) {
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
                per_page: 10,
                max_size: 10,
                pages: 1
            };

            scope.reload = function () {
                var url = '{0}{1}/{2}/{3}/{4}/{5}/{6}/'.format(
                    WMConfig.url.event.event_actions,
                    scope.event.event_id,
                    scope.actionTypeGroup,
                    scope.pager.current_page,
                    scope.pager.per_page,
                    scope.current_sorting.column_name,
                    scope.current_sorting.order.toLowerCase()
                );
                $http.get(url).success(function (data) {
                    scope.actions = data.result.items;
                    scope.actions.forEach(function(action){
                        if(action.type.context){
                            action.ps = new PrintingService("action");
                            action.ps_resolve = function(){
                                return {
                                    action_id: action.id
                                }
                            }
                        }

                    })
                    scope.pager.pages = data.result.pages;
                });
            };
            scope.$on('servicesDataChanged', function() {
                scope.reload();
            });
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
            scope.is_planned_end_date_needed = function () {
                var types_allowed = ['diagnostics', 'lab', 'treatments'];
                return types_allowed.indexOf(scope.actionTypeGroup) !== -1;
            };
            scope.open_action = function (action_id) {
                var url = WMConfig.url.actions.action_html + '?action_id=' + action_id;
                WMWindowSync.openTab(url, scope.update_event);
            };
            scope.open_action_tree = function (at_class) {
                ActionTypeTreeModal.open(
                    scope.event.event_id,
                    scope.event.info.client.info,
                    {
                        at_group: at_class,
                        event_type_id: scope.event.info.event_type.id,
                        contract_id: scope.event.info.contract.id,
                        instant_create: CurrentUser.current_role_in('clinicRegistrator')
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
                        alert('Ошибка удаления действия');
                    });
                });
            };
            scope.open_lab_res_dynamics = function(action){
                LabDynamicsModal.openLabDynamicsModal(scope.event, action);
            };
            scope.action_has_payment = function (action) {
                return Boolean(action.payment);
            };
            scope.reset_sorting();
            scope.reload();
        },
        template:
'<table class="table table-condensed table-hover table-clickable novmargin">\
    <thead wm-sortable-header>\
    <tr>\
        <th width="45%" wm-sortable-column="at_name" on-change-order="sort_by_column(params)">Тип действия</th>\
        <th width="10%" wm-sortable-column="status_code" on-change-order="sort_by_column(params)">Состояние</th>\
        <th width="10%" ng-if="is_planned_end_date_needed()" wm-sortable-column="planned_end_date" on-change-order="sort_by_column(params)">Назначено на</th>\
        <th width="10%" wm-sortable-column="beg_date" on-change-order="sort_by_column(params)">Начало</th>\
        <th width="10%" wm-sortable-column="end_date" on-change-order="sort_by_column(params)">Конец</th>\
        <th width="20%" wm-sortable-column="person_name" on-change-order="sort_by_column(params)">Исполнитель</th>\
        <th width="5%"></th>\
    </tr>\
    </thead>\
    <tbody>\
    <tr ng-repeat="action in actions" ng-class="{\'success\': action.status.code == \'finished\'}">\
        <td ng-click="open_action(action.id)">\
            <span ng-bind="action.name"></span>\
            <span ng-if="action.urgent" class="label"\
                  ng-class="{\'label-danger\': action.status.id < 2, \'label-default\': action.status.id >= 2}">Срочно</span>\
            <span ng-show="action_has_payment(action)" class="text-muted lmargin20"><br>\
            Стоимость: [[ action.payment.sum ]] руб. <span class="glyphicon glyphicon-ok text-success" title="Оплачено"\
            ng-show="action.payment.is_paid"></span>\
        </td>\
        <td ng-click="open_action(action.id)">[[action.status.name]]</td>\
        <td ng-if="is_planned_end_date_needed()" ng-click="open_action(action.id)"><b>[[ action.plannedEndDate | asDate ]]</b></td>\
        <td ng-click="open_action(action.id)">[[ action.begDate | asDate ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.endDate | asDateTime ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.person_text ]]</td>\
        <td class="nowrap">\
            <ui-print-button ps="action.ps" resolve="action.ps_resolve()" ng-if="action.type.context" \
                             lazy-load-context="[[action.type.context]]"></ui-print-button>\
            <button type="button" class="btn btn-sm btn-info" ng-if="actionTypeGroup === \'lab\'" title="Динамика"\
                    ng-click="open_lab_res_dynamics(action)"><span class="glyphicon glyphicon-stats"></span>\
            </button>\
            <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-show="can_delete_action(action)"\
                    ng-click="delete_action(action)"><span class="glyphicon glyphicon-trash"></span>\
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
.service('LabDynamicsModal', ['$modal', '$http', 'WMConfig', function ($modal, $http, WMConfig) {
        return {
        openLabDynamicsModal: function (event, action) {
            var LabResDynamicsCtrl = function ($scope) {
                $scope.date_range = [moment().subtract(5, 'days').toDate(), new Date()];
                $scope.currentDate = new Date();
                $scope.dynamics = [];
                $scope.xAxisTickFormat = function(d){
                    return moment(d).format('DD.MM.YYYY');
                };
                $scope.get_dynamics_data = function() {
                    $http.get(
                        WMConfig.url.event.lab_res_dynamics, {
                            params: {
                                event_id: event.event_id,
                                action_type_id: action.type.id,
                                from_date: $scope.date_range[0],
                                to_date: $scope.date_range[1]
                            }
                        }
                    ).success(function (data) {
                        $scope.dates_list = data.result[0];
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
                backdrop : 'static',
                size: 'lg'
            });
            return instance.result.then(function() {

            });
        }
   }
}])
;