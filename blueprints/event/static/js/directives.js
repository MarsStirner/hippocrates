'use strict';

angular.module('WebMis20.directives').
    directive('wmEventServiceGroup', ['WMEventFormState', 'WMEventController',
        function(WMEventFormState, WMEventController) {
            return {
                restrict: 'A',
                scope: {
                    service: '=model',
                    event: '=',
                    expanded: '='
                },
                link: function (scope, elm, attrs) {
                    scope.formstate = WMEventFormState;
                    scope.eventctrl = WMEventController;

                    scope.amount_disabled = function () {
                        var s = scope.service;
                        return s.fully_paid || (!s.is_new && s.coord_actions && s.coord_actions.length === s.actions.length);
                    };
                    scope.btn_confirm_visible = function () {
                        var s = scope.service;
                        return scope.formstate.is_dms() && (
                             scope.formstate.is_new() && !s.coord_person_id ||
                                 (!scope.formstate.is_new() && (!s.coord_actions || s.coord_actions.length !== s.amount))
                            );
                    };
                    scope.btn_cancel_confirm_visible = function () {
                        var s = scope.service;
                        return scope.formstate.is_dms() && (
                            scope.formstate.is_new() && s.coord_person_id ||
                                (!scope.formstate.is_new() && s.coord_actions && s.coord_actions.length === s.amount)
                            );
                    };
                    scope.btn_delete_visible = function () {
                        return true; //todo
                        return !scope.action.is_paid_for() && !scope.action.is_confirmed() && true; // todo: action not closed
                        //!(service.fully_paid || service.partially_paid || service.coord_actions.length)
                    };
                },
                template:
'<td class="sg-expander" ng-click="expanded = !expanded"><span class="glyphicon glyphicon-chevron-[[expanded ? \'down\' : \'right\']]"></span></td>\
<td ng-bind="service.at_code"></td>\
<td ng-bind="service.service_name"></td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm" min="[[service.paid_count || service.coord_actions.length || 1]]"\
           ng-disabled="amount_disabled()" ng-model="service.total_amount"\
           valid-number ng-change="service.sum = service.price * service.amount"/>\
</td>\
<td ng-bind="service.sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать услугу для оплаты" ng-model="action.account" ng-change="change_action_choice_for_payment()">\
</td>\
<td ng-bind="service.coord_count" class="text-right" ng-show="formstate.is_dms()"></td>\
<td ng-bind="service.paid_count" class="text-center" ng-show="formstate.is_paid()"></td>\
<td nowrap>\
    <button type="button" class="btn btn-sm btn-default" title="Согласовать"\
            ng-show="btn_confirm_visible()"\
            ng-click="eventctrl.confirm_service(service)"><span class="glyphicon glyphicon-check"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-default" title="Отменить согласование"\
            ng-show="btn_cancel_confirm_visible()"\
            ng-click="eventctrl.unconfirm_service(service)"><span class="glyphicon glyphicon-remove"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="remove_service(index)"><span class="glyphicon glyphicon-trash"></span>\
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

                    scope.recalculate_sum = function () {
                        scope.action.sum = scope.service.price * scope.action.amount;
                        scope.service.recalculate_sum();
                    };
                    scope.change_action_choice_for_payment = function() {
//                        if ($scope.event.info.id && service.actions.length){
//                            $http.post(
//                                url_for_event_api_service_change_account, {
//                                    actions: service.actions,
//                                    account: service.account
//                                }
//                            ).error(function() {
//                                alert('error');
//                            });
//                        }
                    };

                    scope.amount_disabled = function () {
                        return false;
                    };
                    scope.btn_confirm_visible = function () {
                        return scope.formstate.is_dms() && !scope.action.is_confirmed() && true; // todo: action not closed
                    };
                    scope.btn_cancel_confirm_visible = function () {
                        return scope.formstate.is_dms() && scope.action.is_confirmed() && true; // todo: action not closed
                    };
                    scope.btn_delete_visible = function () {
                        return !scope.action.is_paid_for() && !scope.action.is_confirmed() && true; // todo: action not closed
                    };
                },
                template:
'<td><span class="glyphicon glyphicon-question-sign"></span></td>\
<td ng-bind="service.at_code"></td>\
<td ng-bind="service.service_name"></td>\
<td ng-bind="service.at_name"></td>\
<td ng-bind="service.price" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="col-md-1">\
    <input type="text" class="form-control input-sm" min="1"\
           ng-disabled="amount_disabled(action)" ng-model="action.amount"\
           valid-number ng-change="recalculate_sum()"/>\
</td>\
<td ng-bind="action.is_confirmed()" class="text-right" ng-show="formstate.is_dms()"></td>\
<td ng-bind="action.sum" class="text-right" ng-show="formstate.is_paid()"></td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <input type="checkbox" title="Выбрать услугу для оплаты" ng-model="action.account" ng-change="change_action_choice_for_payment()">\
</td>\
<td class="text-center" ng-show="formstate.is_paid()">\
    <span class="glyphicon" ng-class="{\'glyphicon-ok\': action.is_paid_for(), \'glyphicon-remove\':!action.is_paid_for()}"></span>\
</td>\
<td nowrap>\
    <button type="button" class="btn btn-sm btn-default" title="Согласовать"\
            ng-show="btn_confirm_visible()"\
            ng-click="eventctrl.confirm_service(action)"><span class="glyphicon glyphicon-check"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-default" title="Отменить согласование"\
            ng-show="btn_cancel_confirm_visible()"\
            ng-click="eventctrl.unconfirm_service(service)"><span class="glyphicon glyphicon-remove"></span>\
    </button>\
    <button type="button" class="btn btn-sm btn-danger" title="Убрать из списка услуг"\
            ng-show="btn_delete_visible()"\
            ng-click="remove_service(index)"><span class="glyphicon glyphicon-trash"></span>\
    </button>\
</td>'
            };
        }
    ])
;

