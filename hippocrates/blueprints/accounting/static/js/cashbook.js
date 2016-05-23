'use strict';

var CashBookCtrl = function ($scope, AccountingService, CashBookModalService) {
    $scope.payer = {
        query: '',
        search_processed: false,
        search_result: null
    };
    $scope.invoice = {
        query: '',
        search_processed: false,
        search_result: null
    };

    $scope.performPayerSearch = function (query) {
        $scope.payer.search_processed = false;
        if (!query) {
            $scope.payer.search_result = null;
        } else {
            AccountingService.search_payer(query)
                .then(function (search_result) {
                    $scope.payer.search_result = search_result;
                    $scope.payer.search_processed = true;
                });
        }
    };
    $scope.openPayerInvoices = function (idx) {
        var payer = $scope.payer.search_result[idx];
        AccountingService.search_invoice(undefined, payer.id)
            .then(function (search_result) {
                $scope.clearInvoiceQuery();
                $scope.invoice.search_result = search_result;
                $scope.invoice.search_processed = true;
            });
    };
    $scope.clearPayerQuery = function () {
        $scope.payer.search_result = null;
        $scope.payer.query = '';
    };
    $scope.editPayerBalance = function (idx) {
        var payer = $scope.payer.search_result[idx];
        CashBookModalService.openEditPayerBalance(payer.id)
            .then(function (result) {
                $scope.payer.search_result.splice(idx, 1, result.payer);
            });
    };

    $scope.performInvoiceSearch = function (query) {
        $scope.invoice.search_processed = false;
        if (!query) {
            $scope.invoice.search_result = null;
        } else {
            AccountingService.search_invoice(query)
                .then(function (search_result) {
                    $scope.invoice.search_result = search_result;
                    $scope.invoice.search_processed = true;
                });
        }
    };
    var updateSearchResultItem = function (idx) {
        var invoice = $scope.invoice.search_result[idx];
        AccountingService.get_invoice(invoice.id, {
            repr_type: 'for_payment'
        }).then(function (upd_invoice) {
            $scope.invoice.search_result.splice(idx, 1, upd_invoice);
        });
    };
    $scope.clearInvoiceQuery = function () {
        $scope.invoice.search_result = null;
        $scope.invoice.query = '';
    };
    $scope.processInvoicePayment = function (idx) {
        var invoice = $scope.invoice.search_result[idx];
        CashBookModalService.openProcessInvoicePayment(invoice.id, invoice.contract.payer.id, {
            event_id: invoice.event_id
        })
            .then(function (result) {
                updateSearchResultItem(idx);
            });
    };
    $scope.processInvoiceCancel = function (idx) {
        var invoice = $scope.invoice.search_result[idx];
        CashBookModalService.openProcessInvoiceCancel(invoice.id, invoice.contract.payer.id, {
            event_id: invoice.event_id
        })
            .then(function (result) {
                updateSearchResultItem(idx);
            }, function () {
                updateSearchResultItem(idx);
            });
    };
    $scope.isInvoiceClosed = function (invoice) {
        return invoice.closed;
    };
    $scope.canProcessInvoicePayment = function (invoice) {
        return !$scope.isInvoiceClosed(invoice);
    };
    $scope.canProcessInvoiceCancel = function (invoice) {
        return $scope.isInvoiceClosed(invoice);
    };
    $scope.hasPendingCoordRefund = function (invoice) {
        return Boolean(invoice.coordinated_refund);
    };

};

WebMis20.controller('CashBookCtrl', ['$scope', 'AccountingService', 'CashBookModalService', CashBookCtrl]);
