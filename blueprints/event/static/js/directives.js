'use strict';

angular.module('WebMis20.directives').
    directive('wmEventServiceGroup', ['WMEventFormState', 'WMEventController',
        function(WMEventFormState, WMEventController) {
            return {
                restrict: 'A',
                scope: {
                    service: '=model',
                    event: '=',
                    idx: '=',
                    expanded: '='
                },
                link: function (scope, elm, attrs) {
                    scope.formstate = WMEventFormState;
                    scope.eventctrl = WMEventController;

                    scope.change_print_service = function() {
                        var s = scope.service;
                        if (s.print){
                            s.print = !s.print;
                        } else {
                            s.print = 1;
                        }
                    };
                    scope.coord_all = function (off) {
                        scope.service.coord_all = !Boolean(off);
                    };

                    scope.amount_disabled = function () {
                        var s = scope.service;
                        return s.fully_paid || s.fully_coord;
                    };
                    scope.btn_coordinate_visible = function () {
                        var s = scope.service;
                        return scope.formstate.is_dms() && !s.fully_coord;
                    };
                    scope.btn_cancel_coordinate_visible = function () {
                        var s = scope.service;
                        return scope.formstate.is_dms() && s.fully_coord;
                    };
                    scope.btn_delete_visible = function () {
                        var s = scope.service;
                        return !s.fully_paid && !s.partially_paid && true; // todo: action not closed
                    };
                },
                template:
'<td class="sg-expander" ng-click="expanded = !expanded"><span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span></td>\
<td ng-bind="service.at_code"></td>\
<td ng-bind="service.service_name"></td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm" min="[[service.paid_count || service.coord_actions.length || 1]]" max="100"\
           ng-disabled="amount_disabled()" ng-model="service.total_amount"\
           valid-number alow-float minval="1"/>\
</td>\
<td ng-bind="service.total_sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать для оплаты" ng-model="service.account_all">\
</td>\
<td ng-bind="service.paid_count" class="text-center" ng-show="formstate.is_paid()"></td>\
<td class="text-center">\
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
    <button type="button" class="btn btn-sm btn-default" title="Печатать"\
            ng-show="formstate.is_paid()"\
            ng-click="change_print_service()"><span class="glyphicon" ng-class="{\'glyphicon-unchecked\': !service.print, \'glyphicon-check\': service.print}"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="eventctrl.remove_service(event, idx)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
            };
        }
    ]).
    directive('wmEventServiceRecord', ['WMEventFormState', 'WMEventController',
        function(WMEventFormState, WMEventController) {
            return {
                restrict: 'A',
                scope: {
                    action: '=',
                    service: '=',
                    event: '='
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
                    scope.get_info_text = function () {
                        return 'Осмотр: Идентификатор {0}, Дата {1}'.format(scope.action.action_id, scope.action.beg_date);
                    };

                    scope.amount_disabled = function () {
                        return scope.action.account || scope.action.is_coordinated();
                    };
                    scope.btn_coordinate_visible = function () {
                        return scope.formstate.is_dms() && !scope.action.is_coordinated() && true; // todo: action not closed
                    };
                    scope.btn_cancel_coordinate_visible = function () {
                        return scope.formstate.is_dms() && scope.action.is_coordinated() && true; // todo: action not closed
                    };
                    scope.btn_delete_visible = function () {
                        return !scope.action.is_paid_for() && !scope.action.is_coordinated() && true; // todo: action not closed
                    };
                },
                template:
'<td></td>\
<td ng-bind="service.at_code"></td>\
<td ng-bind="service.service_name"></td>\
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
<td class="text-center">\
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
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="eventctrl.remove_action(event, action, service)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
            };
        }
    ])
;

