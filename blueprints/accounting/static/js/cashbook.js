'use strict';

var CashBookCtrl = function ($scope, CashPaymentModal) {
    $scope.aux = aux;
    $scope.query = "";
    $scope.event_id = null;
    $scope.event = {};
    $scope.alerts = [];

    $scope.set_event = function (selected_event) {
        $scope.event_id = selected_event.id;
        $scope.event = selected_event;
        $scope.open_event(selected_event);
    };

    $scope.open_event = function (event) {
        CashPaymentModal.open(event).then(function (data) {
            $scope.alerts.push({
                text: 'Оплата успешно проведена: {0} руб.'.format(data.payment_sum),
                code: '',
                data: null,
                type: 'success'
            });
        });
    };
};
var CashPaymentModal = function ($modal, RefBookService) {
    return {
        open: function (event) {
            return $modal.open({
                template:
    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
        <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
        <h4 class="modal-title">Приём оплаты</h4>\
    </div>\
    <div class="modal-body modal-scrollable">\
        <form name="paymentForm" class="form-horizontal">\
        <div ui-alert-list="alerts"></div>\
        <div class="form-group">\
            <label for="cur_act" class="col-md-4 control-label">Предыдущий номер акта</label>\
            <div class="col-md-8">\
                <input type="text" id="cur_act" class="form-control" ng-model="model.current_act"\
                    ng-disabled="true" autocomplete="off">\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="new_act" class="col-md-4 control-label">Новый номер акта*</label>\
            <div class="col-md-8">\
                <input type="text" id="new_act" class="form-control" ng-model="model.new_act" autocomplete="off">\
            </div>\
            <span class="text-muted">* Новый номер будет перезаписан вместо предыдущего</span>\
        </div>\
        <hr>\
        <div class="form-group"\
            ng-class="{\'has-error\': paymentForm.pay_date.$invalid}">\
            <label for="pay_date" class="col-md-4 control-label">Дата платежа</label>\
            <div class="col-md-8">\
                <wm-date id="pay_date" name="pay_date" ng-model="model.payment_date" ng-required="true"></wm-date>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="cash_operation" class="col-md-4 control-label">Кассовая операция</label>\
            <div class="col-md-8">\
                <rb-select id="cash_operation" ng-model="model.cash_operation"\
                    placeholder="выберите значение" ref-book="rbCashOperation">\
                </rb-select>\
            </div>\
        </div>\
        <div class="form-group">\
            <label class="col-md-4 control-label">Тип платежа</label>\
            <div class="col-md-8">\
                <div class="radio" ng-repeat="payment_type in rbPaymentType.objects">\
                    <label>\
                        <input type="radio" id="pay_type[[$index]]" ng-model="model.payment_type"\
                            ng-value="payment_type">[[payment_type.name]]\
                    </label>\
                </div>\
            </div>\
        </div>\
        <div class="form-group"\
            ng-class="{\'has-error\': paymentForm.pay_sum.$invalid}">\
            <label for="pay_sum" class="col-md-4 control-label">Сумма платежа</label>\
            <div class="col-md-8">\
                <input type="text" id="pay_sum" name="pay_sum" class="form-control" ng-model="model.payment_sum"\
                    ng-required="true" placeholder="сумма" valid-number min-val="1" autocomplete="off">\
            </div>\
        </div>\
        </form>\
    </div>\
    <div class="modal-footer">\
        <button type="button" class="btn btn-success" ng-disabled="paymentForm.$invalid" ng-click="accept()">Принять оплату</button>\
        <button type="button" class="btn btn-danger" ng-click="$dismiss()">Отменить</button>\
    </div>',
                controller: function ($scope, $http) {
                    $scope.rbCashOperation = new RefBookService.get('rbCashOperation');
                    $scope.rbPaymentType = new RefBookService.get('PaymentType');
                    $scope.model = {
                        current_act: event.contract.coord_text,
                        new_act: null,
                        payment_date: new Date(),
                        cash_operation: null,
                        payment_type: null,
                        payment_sum: null
                    };
                    $scope.alerts = [];
                    $scope.rbPaymentType.get_by_code_async('cash').then(function (pt) {
                        $scope.model.payment_type = pt;
                    });
                    $scope.accept = function () {
                        $http.post(
                            url_api_event_make_payment, {
                                //event_id: event.id,
                                payment_date: moment($scope.model.payment_date).format('YYYY-MM-DD'),
                                cash_operation: $scope.model.cash_operation,
                                payment_type: $scope.model.payment_type,
                                payment_sum: $scope.model.payment_sum,
                                new_act: $scope.model.new_act
                            }
                        ).success(function () {
                            $scope.$close({
                                payment_sum: $scope.model.payment_sum
                            });
                        }).error(function (data, status) {
                            $scope.alerts[0] = {
                                text: 'Произошла ошибка при проведении платежа. Оплата не принята.',
                                code: status,
                                data: null,
                                type: 'danger'
                            };
                        });
                    };
                }
            }).result;
        }
    };
};
WebMis20.controller('CashBookCtrl', ['$scope', 'CashPaymentModal', CashBookCtrl]);
angular.module('WebMis20.services.dialogs').service('CashPaymentModal', [
    '$modal', 'RefBookService', CashPaymentModal]);
