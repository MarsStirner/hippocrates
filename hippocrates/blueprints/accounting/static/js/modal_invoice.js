'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/invoice.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">[[ isNewInvoice() ? "Создание счёта" : "Просмотр счёта" ]]</h4>\
</div>\
<div class="modal-body">\
    <ng-form name="invoiceForm">\
    <div class="row">\
    <div class="col-md-12">\
        <div class="box box-info">\
            <div class="box-body">\
                <div class="row">\
                <div class="col-md-6">\
                    <div class="form-group"\
                        ng-class="{\'has-error\': invoiceForm.number.$invalid}">\
                        <label class="control-label" for="number">Номер счета</label>\
                        <input type="text" class="form-control" ng-model="invoice.number" id="number" name="number"\
                            ng-required="true" autocomplete="off">\
                    </div>\
                    <div class="form-group">\
                        <label for="set_date">Дата формирования</label>\
                        <wm-date ng-model="invoice.set_date" id="set_date"></wm-date>\
                    </div>\
                </div>\
                <div class="col-md-6">\
                    <div class="form-group">\
                        <label for="deed_number">Номер акта</label>\
                        <input type="text" class="form-control" ng-model="invoice.deed_number" id="deed_number">\
                    </div>\
                    <div class="form-group">\
                        <label for="settle_date">Дата погашения</label>\
                        <wm-date ng-model="invoice.settle_date" id="settle_date" ng-disabled="true"></wm-date>\
                    </div>\
                </div>\
                </div>\
                <div class="row">\
                <div class=col-md-12>\
                    <label for="note">Примечание</label>\
                    <textarea ng-model="invoice.note" rows="1" class="form-control" id="note"></textarea>\
                </div>\
                </div>\
            </div>\
        </div>\
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
                    <th style="max-width: 60%">Услуга</th>\
                    <th>Стоимость<br>(руб.)</th>\
                    <th ng-if="isInvoiceWithDiscounts()" style="min-width: 100px">Скидка</th>\
                    <th>Кол-во</th>\
                    <th>Итог (руб.)</th>\
                </tr>\
                </thead>\
                <tbody>\
                <tr ng-repeat="item in invoice.item_list | flattenNested:\'subitem_list\'"\
                    ng-class="getItemRowClass(item)">\
                    <td>\
                        <span ng-style="getLevelIndentStyle(item)" ng-bind="getNumerationText(item)"></span>\
                    </td>\
                    <td>[[ item.service.service_name ]]</td>\
                    <td>[[ item.service.price | moneyCut ]]</td>\
                    <td ng-if="isInvoiceWithDiscounts()">\
                        <ui-select ng-model="item.discount" ext-select-service-discount\
                            ng-change="onDiscountChanged(item)" ng-if="!isInvoiceClosed() && isDiscountAvailable(item)" allow-clear="true"\
                            theme="select2" append-to-body="true" placeholder="...">\
                        </ui-select>\
                        <span ng-if="isInvoiceClosed() && isDiscountAvailable(item)">[[ item.discount.description.short ]]</span>\
                    </td>\
                    <td>[[ item.service.amount ]]</td>\
                    <td>[[ item.sum | moneyCut ]]</td>\
                </tr>\
                </tbody>\
                <tbody>\
                <tr ng-if="showSumWoDiscounts()">\
                    <td colspan="5" class="text-right">Итого без учёта скидок:</td>\
                    <td class="text-left">[[ invoice.sum_wo_discounts ]]</td>\
                </tr>\
                <tr style="font-size: larger; font-weight: bold">\
                    <td colspan="[[isInvoiceWithDiscounts() ? 5 : 4]]" class="text-right">Итого:</td>\
                    <td class="text-left">[[ invoice.total_sum ]]</td>\
                </tr>\
                </tbody>\
                </table>\
                \
                <div class="row tmargin20" ng-if="!isInvoiceClosed()">\
                    <div class="form-group col-md-9">\
                        <label for="new_discount">Выбрать скидку</label>\
                        <div class="row">\
                        <div class="col-md-9">\
                        <ui-select ng-model="newDiscount.val" ext-select-service-discount\
                            allow-clear="true" id="new_discount"\
                            theme="select2" append-to-body="true" placeholder="Выберите скидку">\
                        </ui-select>\
                        </div>\
                        <div class="cold-md-3">\
                            <button type="button" class="btn btn-info" ng-click="applyDiscounts()">Применить ко всем</button>\
                        </div>\
                        </div>\
                    </div>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
    </ng-form>\
    <!-- <pre>[[ invoice | json ]]</pre> -->\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-danger pull-left" ng-click="deleteAndClose()"\
        ng-if="btnDeleteAvailable()">Удалить</button>\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
    <ui-print-button ps="ps" resolve="ps_resolve()" ng-if="!isNewInvoice()"\
        fast-print="true"></ui-print-button>\
    <button type="button" class="btn btn-primary" ng-disabled="invoiceForm.$invalid"\
        ng-click="saveAndClose()" ng-if="btnSaveAvailable()">Сохранить</button>\
</div>');
}]);


var InvoiceModalCtrl = function ($scope, $filter, AccountingService, PrintingService, invoice, event) {
    $scope.invoice = invoice;
    $scope.event = event;
    $scope.newDiscount = {
        val: null
    };

    $scope.isNewInvoice = function () {
        return !$scope.invoice.id;
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
        if (item.ui_attrs.idx % 2 !== 0) return 'bg-muted';
        else return '';
    };
    $scope.saveAndClose = function () {
        $scope.save_invoice().then(function (updInvoice) {
            $scope.$close({
                status: 'ok',
                invoice: updInvoice
            });
        });
    };
    $scope.save_invoice = function () {
        return AccountingService.save_invoice(
            $scope.invoice
        );
    };
    $scope.deleteAndClose = function () {
        $scope.delete_invoice().then(function () {
            $scope.$close({
                status: 'del'
            });
        });
    };
    $scope.delete_invoice = function () {
        return AccountingService.delete_invoice(
            $scope.invoice
        );
    };
    $scope.isInvoiceClosed = function () {
        return $scope.invoice.closed;
    };
    $scope.isInvoiceWithDiscounts = function () {
        return $scope.invoice.can_add_discounts;
    };
    $scope.onDiscountChanged = function (item) {
        // при очистке значения виджета очищается атрибут модели
        if (item.discount === undefined) {
            item.discount = null;
        }
        $scope.applyDiscount();
    };
    $scope.applyDiscount = function () {
        AccountingService.calc_invoice_sum($scope.invoice)
            .then(function (new_invoice) {
                $scope.invoice = new_invoice;
            });
    };
    var traverseApplyDiscounts = function (item) {
        if ($scope.isDiscountAvailable(item)) {
            item.discount = angular.copy($scope.newDiscount.val);
        }

        angular.forEach(item.subitem_list, function (subitem) {
            traverseApplyDiscounts(subitem);
        });
    };
    $scope.applyDiscounts = function () {
        angular.forEach($scope.invoice.item_list, function (item) {
            traverseApplyDiscounts(item);
        });
        AccountingService.calc_invoice_sum($scope.invoice)
            .then(function (new_invoice) {
                $scope.invoice = new_invoice;
            });
    };
    $scope.showSumWoDiscounts = function () {
        return $scope.invoice.sum_wo_discounts !== $scope.invoice.total_sum;
    };
    $scope.isDiscountAvailable = function (item) {
        if (item.ui_attrs.level === 0) {
            return !item.service.is_accumulative_price;
        } else {
            var root_idx = item.ui_attrs.root_idx,
                root_item = $scope.invoice.item_list[root_idx];
            return root_item.service.is_accumulative_price;
        }
    };
    $scope.ps_resolve = function () {
        return {
            invoice_id: $scope.invoice.id,
            event_id: $scope.event.info.id
        }
    };
    $scope.btnDeleteAvailable = function () {
        return !$scope.event.ro && !$scope.isInvoiceClosed();
    };
    $scope.btnSaveAvailable = function () {
        return !$scope.event.ro && !$scope.isInvoiceClosed();
    };

    $scope.init = function () {
        $scope.ps = new PrintingService("invoice");
        $scope.ps.set_context('invoice');
    };

    $scope.init();
};


WebMis20.controller('InvoiceModalCtrl', ['$scope', '$filter', 'AccountingService', 'PrintingService', InvoiceModalCtrl]);