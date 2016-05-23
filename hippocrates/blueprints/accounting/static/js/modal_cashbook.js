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
            finance_operation_type: operation
        });
        return AccountingService.make_finance_transaction($scope.trx_type, data);
    };

    $scope.init = function () {
        var trxOperations = RefBookService.get('FinanceOperationType');
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
    <h4 class="modal-title">\
        <span>Оплата счёта</span>\
    </h4>\
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
                            <input type="checkbox" ng-model="deposit_payment.checked" ng-change="setDepositSum()"> Внести сумму\
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
                <tr ng-repeat="item in invoice.item_list | flattenNested:\'subitem_list\'">\
                    <td>\
                        <span ng-style="getLevelIndentStyle(item)" ng-bind="getNumerationText(item)"></span>\
                    </td>\
                    <td>[[ item.service.service_name ]]</td>\
                    <td>[[ item.price ]]</td>\
                    <td>[[ item.amount ]]</td>\
                    <td>[[ item.sum ]]</td>\
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
    <ui-print-button ps="ps" resolve="ps_resolve()" fast-print="true"></ui-print-button>\
    <button type="button" class="btn btn-success" ng-disabled="invoicePaymentForm.$invalid"\
        ng-click="saveAndClose()">Оплатить</button>\
</div>');
}]);


var CashbookInvoiceModalCtrl = function ($scope, $q, $filter, AccountingService, RefBookService, PrintingService,
        payer, trxes, invoice, options) {
    $scope.payer = null;
    $scope.trxes = null;
    $scope.invoice = null;
    $scope.role = null;
    $scope.cancel_coordinated = {
        checked: false
    };
    $scope.deposit_payment = {
        checked: false
    };
    $scope.ops = {
        balance_in: null,
        invoice_pay: null
    };
    $scope.trx_type = null;
    $scope.ps_resolve = function () {
        return {
            invoice_id: $scope.invoice.id,
            event_id: options && options.event_id
        }
    };
    $scope.ps = new PrintingService("invoice");
    $scope.ps.set_context('invoice');

    $scope.isDepositPayment = function () {
        return $scope.deposit_payment.checked;
    };
    $scope.setDepositSum = function () {
        if ($scope.deposit_payment.checked) {
            $scope.trxes.payer_balance_trx.sum = $scope.invoice.total_sum;
        }
    };
    $scope.getLevelIndentStyle = function (item) {
        return {
            'margin-left': '{0}px'.format(10 * item.ui_attrs.level)
        }
    };
    $scope.getNumerationText = function (item) {
        if (item.ui_attrs.level === 0) return item.ui_attrs.idx + 1;
        else return '‒';
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
            finance_operation_type: $scope.ops.invoice_pay
        });
        if ($scope.isDepositPayment()) {
            data.payer_balance_trx = angular.extend($scope.trxes.payer_balance_trx, {
                finance_operation_type: $scope.ops.balance_in
            })
        }
        return AccountingService.make_finance_transaction_invoice($scope.trx_type, data);
    };

    $scope.init = function () {
        var trxOperations = RefBookService.get('FinanceOperationType');
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

WebMis20.controller('CashbookInvoiceModalCtrl', ['$scope', '$q', '$filter', 'AccountingService', 'RefBookService',
    'PrintingService', CashbookInvoiceModalCtrl]);


WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/cashbook_invoice_refund.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">\
        <span>Отмена оплаты счёта</span>\
    </h4>\
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
            <dt ng-if="payer">Плательщик</dt>\
            <dd ng-if="payer"><span>[[ payer.short_descr ]]</span>, \
                <span>Баланс: <span style="font-size: larger; font-weight: bold">[[ payer.balance ]]</span> <i class="fa fa-rub"></i></span></dd>\
            <dt>Сумма счёта</dt>\
            <dd>[[ invoice.total_sum ]] <i class="fa fa-rub"></i></dd>\
        </dl>\
    </div>\
    </div>\
    <div class="row">\
    <div class="col-md-12">\
        <ng-form name="invoiceCancelForm" class="form-horizontal" ng-show="!inCoordinateOnlyMode() && pendingCoordRefund()">\
            <div class="form-group" ng-class="{\'has-error\': invoiceCancelForm.pay_type.$invalid}">\
                <label for="sum" class="col-md-3 control-label">Способ</label>\
                <div class="col-md-7">\
                    <rb-select ng-model="refund.pay_type" ref-book="rbPayType" id="pay_type" name="pay_type"\
                        ng-required="true"></rb-select>\
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
                <div class="text-warning text-bold" ng-if="pendingCoordRefund() || newCoordRefund()">\
                    <span ng-if="pendingCoordRefund()"><i class="fa fa-exclamation-circle rmargin10"></i>\
                    По счёту имеется согласованный возврат оплаты.<span\
                        ng-if="!inCoordinateOnlyMode()"> Проведите возврат денежных средств.</span></span>\
                    <span class="text-black pull-right" ng-if="newCoordRefund()">Сумма возврата: <span\
                        style="font-size: larger; font-weight: bold">[[ refund.refund_sum ]]</span> <i class="fa fa-rub"></i></span>\
                </div>\
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
                    <th>&nbsp</th>\
                </tr>\
                </thead>\
                <tbody>\
                <tr ng-repeat="item in invoice.item_list | flattenNested:\'subitem_list\'"\
                    ng-class="getItemRowClass(item)">\
                    <td>\
                        <span ng-style="getLevelIndentStyle(item)" ng-bind="getNumerationText(item)"></span>\
                    </td>\
                    <td>[[ item.service.service_name ]]</td>\
                    <td>[[ item.price ]]</td>\
                    <td>[[ item.amount ]]</td>\
                    <td>[[ item.sum ]]</td>\
                    <td>\
                        <wm-checkbox select-all="selected_items" key="item" ng-if="canBeCoordinated(item)"/>\
                    </td>\
                </tr>\
                </tbody>\
                <tbody>\
                <tr>\
                    <td colspan="4" class="text-right">Итого с учётом возвратов:<br>Уже возвратов на сумму:</td>\
                    <td class="text-left">[[ refund.invoice_refunded_sum ]]<br>[[ invoice.refunds_sum ]]</td>\
                </tr>\
                </tbody>\
                <tbody>\
                <tr style="font-size: larger; font-weight: bold">\
                    <td colspan="4" class="text-right">Сумма возврата:</td>\
                    <td class="text-left">[[ refund.refund_sum ]]</td>\
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
    <ui-print-button ps="ps" resolve="ps_resolve()" fast-print="true"></ui-print-button>\
    <button type="button" class="btn btn-warning" ng-disabled="!btnCoordinateEnabled()"\
            ng-click="coordinateRefund()" ng-if="!pendingCoordRefund()">Согласовать возврат</button>\
    <button type="button" class="btn btn-danger"\
            ng-click="cancelCoordinatedRefund()" ng-if="pendingCoordRefund()">Отменить согласование</button>\
    <button type="button" class="btn btn-warning" ng-disabled="invoiceCancelForm.$invalid || !btnRefundPaymentEnabled()"\
            ng-click="processRefund()" ng-if="!inCoordinateOnlyMode() && pendingCoordRefund()">Вернуть сумму</button>\
</div>');
}]);


var CashbookInvoiceRefundModalCtrl = function ($scope, $q, $filter, AccountingService, RefBookService, PrintingService,
        SelectAll, payer, invoice, options) {
    $scope.payer = null;
    $scope.invoice = null;
    $scope.pendingCoordItemsIds = [];
    $scope.refund = {
        pay_type: undefined,
        refund_sum: undefined,
        invoice_refunded_sum: undefined
    };
    $scope.selected_items = new SelectAll([]);
    $scope.ps_resolve = function () {
        return {
            invoice_id: $scope.invoice.id,
            event_id: options && options.event_id
        }
    };
    $scope.ps = new PrintingService("invoice");
    $scope.ps.set_context('invoice');

    var setInvoice = function (invoice) {
        $scope.invoice = invoice;
        $scope.pendingCoordItemIds = safe_traverse(invoice, ['coordinated_refund', 'item_list'], [])
            .map(function (item) {
                return item.id
            });
        $scope.refundedItemIds = [];
        angular.forEach(invoice.refund_list, function (refund) {
            angular.forEach(refund.item_list, function (item) {
                $scope.refundedItemIds.push(item.id);
            });
        });
        $scope.lockedItemIds = $scope.pendingCoordItemIds.concat($scope.refundedItemIds);
        var available_items = $filter('flattenNested')(invoice.item_list, 'subitem_list')
            .filter(function (item) {
                return !$scope.lockedItemIds.has(item.id);
            });

        $scope.selected_items.setSource(available_items);
        $scope.selected_items.selectNone();
    };

    $scope.inCoordinateOnlyMode = function () {
        return Boolean(options && options.coordOnly);
    };
    $scope.getLevelIndentStyle = function (item) {
        return {
            'margin-left': '{0}px'.format(10 * item.ui_attrs.level)
        }
    };
    $scope.getNumerationText = function (item) {
        if (item.ui_attrs.level === 0) return item.ui_attrs.idx + 1;
        else return '‒';
    };
    $scope.getItemRowClass = function (item) {
        if ($scope.pendingCoordItemIds.has(item.id)) return 'bg-warning';
        else if ($scope.refundedItemIds.has(item.id)) return 'bg-muted text-striked';
        else return '';
    };
    $scope.canBeCoordinated = function (item) {
        return !$scope.pendingCoordItemIds.length && !$scope.lockedItemIds.has(item.id);
    };
    $scope.pendingCoordRefund = function () {
        return Boolean(safe_traverse($scope, ['invoice', 'coordinated_refund']));
    };
    $scope.newCoordRefund = function () {
        return Boolean($scope.refund.refund_sum);
    };
    $scope.btnCoordinateEnabled = function () {
        return !$scope.pendingCoordRefund() && $scope.selected_items.any();
    };
    $scope.btnRefundPaymentEnabled = function () {
        return $scope.pendingCoordRefund();
    };
    var recalcSums = function () {
        var selected_sum = $scope.selected_items.selected()
                .reduce(function (prev, cur) {
                    if (cur.service.is_accumulative_price) return prev;
                    else return prev + parseFloat(cur.sum);
                }, 0),
            unselected_sum = $scope.selected_items.unselected()
                .reduce(function (prev, cur) {
                    if (cur.service.is_accumulative_price) return prev;
                    else return prev + parseFloat(cur.sum);
                }, 0);
        if ($scope.pendingCoordRefund()) {
            $scope.refund.refund_sum = $scope.invoice.coordinated_refund.payment.refund_total_sum;
        } else {
            $scope.refund.refund_sum = selected_sum.toFixed(2);
        }
        $scope.refund.invoice_refunded_sum = unselected_sum.toFixed(2);
    };
    $scope.$watch('selected_items._selected', function (newVal) {
        recalcSums();
    }, true);

    $scope.coordinateRefund = function () {
        AccountingService.coordinate_refund(invoice, $scope.selected_items.selected())
            .then(function (new_refund) {
                AccountingService.get_invoice(invoice.id).then(setInvoice);
            });
    };
    $scope.cancelCoordinatedRefund = function () {
        AccountingService.cancel_coordinated_refund(invoice)
            .then(function (result) {
                AccountingService.get_invoice(invoice.id).then(setInvoice);
            });
    };
    $scope.processRefund = function () {
        AccountingService.process_refund(invoice, $scope.refund.pay_type)
            .then(function (result) {
                $scope.$close({
                    status: 'ok'
                });
            });
    };

    $scope.init = function () {
        $scope.payer = payer;
        setInvoice(invoice);
    };

    $scope.init();
};

WebMis20.controller('CashbookInvoiceRefundModalCtrl', ['$scope', '$q', '$filter', 'AccountingService', 'RefBookService',
    'PrintingService', 'SelectAll', CashbookInvoiceRefundModalCtrl]);