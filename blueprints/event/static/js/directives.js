'use strict';

angular.module('WebMis20.directives').
    directive('wmEventServiceGroup', ['WMEventFormState', 'WMEventController', 'ActionTypeTreeModal',
        function(WMEventFormState, WMEventController, ActionTypeTreeModal) {
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
                    scope.eventctrl = WMEventController;

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
                            planned_end_date: ped
                        };
                        ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
                            scope.service.actions.forEach(function (act) {
                                if (!act.is_closed()) {
                                    act.assigned = model.assigned;
                                    act.planned_end_date = model.planned_end_date;
                                }
                            });
                        });
                    };

                    scope.amount_disabled = function () {
                        return scope.service.fully_paid || scope.service.fully_coord;
                    };
                    scope.btn_coordinate_visible = function () {
                        return !scope.service.fully_coord && !scope.service.all_actions_closed;
                    };
                    scope.btn_cancel_coordinate_visible = function () {
                        return scope.service.fully_coord && !scope.service.all_actions_closed;
                    };
                    scope.btn_delete_visible = function () {
                        var s = scope.service;
                        return !(
                            s.fully_paid || s.partially_paid || s.fully_coord || s.partially_coord ||
                            scope.service.all_actions_closed
                        );
                    };
                    scope.lab_components_disabled = function () {
                        return scope.service.fully_paid || scope.service.fully_coord || scope.service.all_actions_closed;
                    };
                },
                template:
'<td class="sg-expander" ng-click="expanded = !expanded"><span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span></td>\
<td ng-bind="service.at_code"></td>\
<td>\
    [[service.service_name]]\
    <a href="javascript:0" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
        ng-disabled="lab_components_disabled()">Выбрать назначаемые исследования</a>\
</td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm"\
           ng-disabled="amount_disabled()" ng-model="service.total_amount"\
           valid-number min-val="get_min_amount()" max-val="get_max_amount()"/>\
</td>\
<td ng-bind="service.total_sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать для оплаты" ng-model="service.account_all">\
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
<td nowrap>\
    <button type="button" class="btn btn-sm btn-danger" title="Удалить услуги"\
            ng-show="btn_delete_visible()"\
            ng-click="eventctrl.remove_service(event, idx)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
            };
        }
    ]).
    directive('wmEventServiceRecord', ['WMEventFormState', 'WMEventController', 'ActionTypeTreeModal', '$filter',
        function(WMEventFormState, WMEventController, ActionTypeTreeModal, $filter) {
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
                    scope.eventctrl = WMEventController;

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
                            planned_end_date: scope.action.planned_end_date
                        };
                        ActionTypeTreeModal.openAppointmentModal(model, true).then(function () {
                            scope.action.assigned = model.assigned;
                            scope.action.planned_end_date = model.planned_end_date;
                        });
                    };
                    scope.get_info_text = function () {
                        var msg = [
                            'Идентификатор: ' + scope.action.action_id,
                            'Дата начала: ' + $filter('asDateTime')(scope.action.beg_date),
                            'Дата окончания: ' + $filter('asDateTime')(scope.action.end_date),
                            'Статус: ' + scope.action.status,
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
                        return scope.action.account || scope.action.is_coordinated();
                    };
                    scope.btn_coordinate_visible = function () {
                        return !scope.action.is_coordinated() && !scope.action.is_closed();
                    };
                    scope.btn_cancel_coordinate_visible = function () {
                        return scope.action.is_coordinated() && !scope.action.is_closed();
                    };
                    scope.btn_delete_visible = function () {
                        return !(scope.action.is_paid_for() || scope.action.is_coordinated() || scope.action.is_closed());
                    };
                    scope.lab_components_disabled = function () {
                        return scope.action.account || scope.action.is_coordinated() || scope.action.is_closed();
                    };
                },
                template:
'<td></td>\
<td ng-bind="service.at_code"></td>\
<td>\
    [[service.service_name]]\
    <a  href="javascript:0" class="btn btn-link nomarpad" ng-click="open_assignments()" ng-if="service.is_lab"\
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
    <input type="checkbox" title="Выбрать услугу для оплаты" ng-model="action.account" ng-change="change_action_choice_for_payment()">\
</td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_paid_for(), \'glyphicon-remove\':!action.is_paid_for()}"></span>\
</td>\
<td class="text-center" ng-show="formstate.is_dms()">\
    <button type="button" class="btn btn-sm btn-default" title="Согласовать"\
            ng-show="btn_coordinate_visible()"\
            ng-click="eventctrl.coordinate(action)"><span class="glyphicon glyphicon-check"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-default" title="Отменить согласование"\
            ng-show="btn_cancel_coordinate_visible()"\
            ng-click="eventctrl.coordinate(action, \'off\')"><span class="glyphicon glyphicon-remove"></span>\
    </button>\
</td>\
<td class="text-center" ng-show="formstate.is_dms()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_coordinated(), \'glyphicon-remove\':!action.is_coordinated()}"></span>\
</td>\
<td nowrap>\
    <span class="glyphicon glyphicon-info-sign"\
        popover-trigger="mouseenter" popover-popup-delay=\'1000\' popover-placement="left" popover="[[get_info_text()]]"></span>\
    <ui-print-button ps="get_ps()" resolve="get_ps_resolve()" ng-if="action.action_id"></ui-print-button>\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="eventctrl.remove_action(event, action, service)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
            };
        }
    ])
;

