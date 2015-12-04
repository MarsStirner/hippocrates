'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/cashbook_payer_balance.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Баланс плательщика</h4>\
    <span class="text-muted">[[ payer.full_descr ]]</span>\
</div>\
<div class="modal-body">\
    <div class="row">\
    <div class="col-md-12">\
    <ng-form name="payerBalanceForm" class="form-horizontal">\
        <div class="form-group">\
            <label for="balance" class="col-md-3 control-label">Текущий баланс</label>\
            <div class="col-md-9">\
                <div class="input-group">\
                <input type="text" class="form-control text-right" id="balance" ng-model="payer.balance" readonly>\
                <span class="input-group-addon"><i class="fa fa-rub"></i></span>\
                </div>\
            </div>\
        </div>\
        <hr>\
        <div class="form-group"\
            ng-class="{\'has-error\': payerBalanceForm.pay_type.$invalid}">\
            <label for="sum" class="col-md-3 control-label">Способ</label>\
            <div class="col-md-9">\
                <rb-select ng-model="trx.pay_type" ref-book="rbPayType" id="pay_type" name="pay_type"\
                    ng-required="true"></rb-select>\
            </div>\
        </div>\
        <div class="form-group"\
            ng-class="{\'has-error\': payerBalanceForm.sum.$invalid}">\
            <label for="sum" class="col-md-3 control-label">Сумма</label>\
            <div class="col-md-9">\
                <div class="input-group">\
                <input type="text" class="form-control text-right" id="sum" name="sum" ng-model="trx.sum"\
                    valid-number valid-number-float ng-required="true">\
                <span class="input-group-addon"><i class="fa fa-rub"></i></span>\
                </div>\
            </div>\
        </div>\
    </ng-form>\
    </div>\
    </div>\
    <!-- <pre>[[ payer | json ]]</pre>\
    <pre>[[ trx | json ]]</pre> -->\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default rmargin10" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-danger" ng-disabled="payerBalanceForm.$invalid"\
        ng-click="saveAndClose(ops.balance_out)">Вернуть сумму</button>\
    <button type="button" class="btn btn-success" ng-disabled="payerBalanceForm.$invalid"\
        ng-click="saveAndClose(ops.balance_in)">Внести сумму</button>\
</div>');
}]);


var CashbookPayerModalCtrl = function ($scope, $q, AccountingService, RefBookService, payer, trx) {
    $scope.payer = null;
    $scope.trx = null;
    $scope.ops = {
        balance_in: null,
        balance_out: null
    };
    $scope.trx_type = null;

    $scope.saveAndClose = function (operation) {
        $scope.make_trx(operation).then(function (payer) {
            $scope.$close({
                status: 'ok',
                payer: payer
            });
        });
    };
    $scope.make_trx = function (operation) {
        var data = angular.extend($scope.trx, {
            contragent_id: $scope.payer.id,
            finance_operation: operation
        });
        return AccountingService.make_finance_transaction($scope.trx_type, data);
    };

    $scope.init = function () {
        var trxOperations = RefBookService.get('FinanceTransactionOperation');
        var trxTypes = RefBookService.get('FinanceTransactionType');
        $q.all([trxOperations.loading, trxTypes.loading])
            .then(function () {
                $scope.payer = payer;
                $scope.trx = trx;
                $scope.ops.balance_in = trxOperations.get_by_code('payer_balance_in');
                $scope.ops.balance_out = trxOperations.get_by_code('payer_balance_out');
                $scope.trx_type = trxTypes.get_by_code('payer_balance');
            });
    };

    $scope.init();
};

WebMis20.controller('CashbookPayerModalCtrl', ['$scope', '$q', 'AccountingService', 'RefBookService',
    CashbookPayerModalCtrl]);


WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/cashbook_invoice.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Оплата счёта</h4>\
</div>\
<div class="modal-body">\
    <div class="row">\
    <div class="col-md-offset-1 col-md-5">\
        <dl class="dl-horizontal">\
            <dt>Счёт</dt>\
            <dd>№ [[ invoice.number ]]</dd>\
            <dt>Дата формирования</dt>\
            <dd>[[ invoice.set_date | asDate ]]</dd>\
            <dt>Дата погашения</dd>\
            <dd>[[ invoice.settle_date | asDate ]]</dt>\
        </dl>\
    </div>\
    <div class="col-md-5">\
        <dl class="dl-horizontal">\
            <dt>Плательщик</dt>\
            <dd><span>[[ payer.short_descr ]]</span>, \
                <span>Баланс: <span style="font-size: larger; font-weight: bold">[[ payer.balance ]]</span> <i class="fa fa-rub"></i></span></dd>\
            <dt>Сумма счёта</dt>\
            <dd>[[ invoice.total_sum ]] <i class="fa fa-rub"></i></dd>\
        </dl>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
    <ng-form name="invoicePaymentForm" class="form-horizontal">\
        <div class="form-group">\
            <div class="col-sm-offset-3 col-sm-7">\
                <div class="checkbox">\
                    <label>\
                        <input type="checkbox" ng-model="deposit_payment.checked"> Внести сумму\
                    </label>\
                </div>\
            </div>\
        </div>\
        <div class="form-group" ng-show="isDepositPayment()"\
            ng-class="{\'has-error\': invoicePaymentForm.pay_type.$invalid}">\
            <label for="sum" class="col-md-3 control-label">Способ</label>\
            <div class="col-md-7">\
                <rb-select ng-model="trxes.payer_balance_trx.pay_type" ref-book="rbPayType" id="pay_type" name="pay_type"\
                    ng-required="isDepositPayment()"></rb-select>\
            </div>\
        </div>\
        <div class="form-group" ng-show="isDepositPayment()"\
            ng-class="{\'has-error\': invoicePaymentForm.pb_sum.$invalid}">\
            <label for="pb_sum" class="col-md-3 control-label">Вносимая сумма</label>\
            <div class="col-md-7">\
                <div class="input-group">\
                <input type="text" class="form-control text-right" id="pb_sum" name="pb_sum" ng-model="trxes.payer_balance_trx.sum"\
                    valid-number valid-number-float ng-required="isDepositPayment()">\
                <span class="input-group-addon"><i class="fa fa-rub"></i></span>\
                </div>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="invoice_sum" class="col-md-3 control-label">Оплачиваемая сумма</label>\
            <div class="col-md-7">\
                <div class="input-group">\
                <input type="text" class="form-control text-right" id="invoice_sum" name="invoice_sum" ng-model="trxes.invoice_trx.sum"\
                    valid-number valid-number-float readonly>\
                <span class="input-group-addon"><i class="fa fa-rub"></i></span>\
                </div>\
                <span class="text-warning" ng-show="!isDepositPayment()">Оплачивается с текущего баланса плательщика</span>\
            </div>\
        </div>\
    </ng-form>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-header with-border">\
                <h3 class="box-title">Позиции счета</h3>\
            </div>\
            <div class="box-body">\
                <table class="table">\
                <thead>\
                <tr>\
                    <th>№</th>\
                    <th>Услуга</th>\
                    <th>Стоимость (руб.)</th>\
                    <th>Кол-во</th>\
                    <th>Итог (руб.)</th>\
                </tr>\
                </thead>\
                <tbody>\
                <tr ng-repeat="item in invoice.item_list">\
                    <td>[[ $index + 1 ]]</td>\
                    <td>[[ item.service.service_name ]]</td>\
                    <td>[[ item.service.price ]]</td>\
                    <td>[[ item.service.amount ]]</td>\
                    <td>[[ item.service.sum ]]</td>\
                </tr>\
                </tbody>\
                <tbody>\
                <tr>\
                    <td colspan="4" class="text-right">Итого:</td>\
                    <td class="text-left">[[ invoice.total_sum ]]</td>\
                </tr>\
                </tbody>\
                </table>\
            </div>\
        </div>\
    </div>\
    </div>\
    <!-- <pre>[[ trxes | json ]]</pre> -->\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default rmargin10" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <button type="button" class="btn btn-success" ng-disabled="invoicePaymentForm.$invalid"\
        ng-click="saveAndClose()">Оплатить</button>\
</div>');
}]);


var CashbookInvoiceModalCtrl = function ($scope, $q, AccountingService, RefBookService, payer, trxes, invoice) {
    $scope.payer = null;
    $scope.trxes = null;
    $scope.invoice = null;
    $scope.deposit_payment = {
        checked: false
    };
    $scope.ops = {
        balance_in: null,
        invoice_pay: null
    };
    $scope.trx_type = null;

    $scope.isDepositPayment = function () {
        return $scope.deposit_payment.checked;
    };
    $scope.saveAndClose = function () {
        $scope.make_invoice_trxes().then(function (invoice) {
            $scope.$close({
                status: 'ok',
                invoice: invoice
            });
        });
    };
    $scope.make_invoice_trxes = function () {
        var data = {};
        data.invoice_trx = angular.extend($scope.trxes.invoice_trx, {
            finance_operation: $scope.ops.invoice_pay
        });
        if ($scope.isDepositPayment()) {
            data.payer_balance_trx = angular.extend($scope.trxes.payer_balance_trx, {
                finance_operation: $scope.ops.balance_in
            })
        }
        return AccountingService.make_finance_transaction_invoice($scope.trx_type, data);
    };

    $scope.init = function () {
        var trxOperations = RefBookService.get('FinanceTransactionOperation');
        var trxTypes = RefBookService.get('FinanceTransactionType');
        $q.all([trxOperations.loading, trxTypes.loading])
            .then(function () {
                $scope.payer = payer;
                $scope.trxes = trxes;
                $scope.invoice = invoice;
                if (parseFloat($scope.payer.balance) < parseFloat($scope.invoice.total_sum)) {
                    $scope.deposit_payment.checked = true;
                }
                $scope.ops.balance_in = trxOperations.get_by_code('payer_balance_in');
                $scope.ops.invoice_pay = trxOperations.get_by_code('invoice_pay');
                $scope.trx_type = trxTypes.get_by_code('invoice');
            });
    };

    $scope.init();
};

WebMis20.controller('CashbookInvoiceModalCtrl', ['$scope', '$q', 'AccountingService', 'RefBookService',
    CashbookInvoiceModalCtrl]);