'use strict';

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal/accounting/invoice.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Создание счета</h4>\
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
                        <input type="text" class="form-control" ng-model="invoice.number" id="number"\
                            ng-required="true">\
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
    </ng-form>\
    <!-- <pre>[[ invoice | json ]]</pre> -->\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-danger pull-left" ng-click="deleteAndClose()">Удалить</button>\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отменить</button>\
    <button type="button" class="btn btn-primary" ng-disabled="invoiceForm.$invalid" ng-click="saveAndClose()">Сохранить</button>\
</div>');
}]);


var InvoiceModalCtrl = function ($scope, $filter, AccountingService, invoice) {
    $scope.invoice = invoice;
    $scope.saveAndClose = function () {
        if (!$scope.invoiceForm.$valid) return;
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

    $scope.init = function () { };

    $scope.init();
};


WebMis20.controller('InvoiceModalCtrl', ['$scope', '$filter', 'AccountingService', InvoiceModalCtrl]);