'use strict';

WebMis20.service('ContractModalService', ['$modal', function ($modal) {
    return {
        openEdit: function (contract, client) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal/accounting/contract_edit.html',
                controller: ContractModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    contract: function () {
                        return contract
                    },
                    client: function () {
                        return client
                    }
                }
            });
            return instance.result;
        }
    }
}]);

WebMis20.service('InvoiceModalService', ['$modal', 'AccountingService', function ($modal, AccountingService) {
    return {
        openNew: function (service_list, contract_id, event) {
            return AccountingService.get_invoice(undefined, {
                service_list: service_list,
                contract_id: contract_id
            }).then(function (newInvoice) {
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal/accounting/invoice.html',
                    controller: InvoiceModalCtrl,
                    backdrop: 'static',
                    size: 'lg',
                    windowClass: 'modal-scrollable',
                    resolve: {
                        invoice: function () {
                            return newInvoice
                        },
                        event: function () {
                            return event;
                        }
                    }
                });
                return instance.result;
            });
        },
        openEdit: function (invoice, event) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal/accounting/invoice.html',
                controller: InvoiceModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    invoice: function () {
                        return invoice
                    },
                    event: function () {
                        return event
                    }
                }
            });
            return instance.result;
        }
    }
}]);

WebMis20.service('CashBookModalService', ['$modal', '$q', 'AccountingService',
        function ($modal, $q, AccountingService) {
    return {
        openEditPayerBalance: function (contragent_id) {
            var finance_trx_promise = AccountingService.get_new_finance_trx(contragent_id),
                payer_promise = AccountingService.get_contragent_payer(contragent_id);
            return $q.all([finance_trx_promise, payer_promise])
                .then(function (data) {
                    var trx = data[0],
                        payer = data[1];
                    var instance = $modal.open({
                        templateUrl: '/WebMis20/modal/accounting/cashbook_payer_balance.html',
                        controller: CashbookPayerModalCtrl,
                        backdrop: 'static',
                        resolve: {
                            payer: function () {
                                return payer;
                            },
                            trx: function () {
                                return trx;
                            }
                        }
                    });
                    return instance.result;
            });
        },
        openProcessInvoicePayment: function (invoice_id, contragent_id) {
            var finance_trx_promise = AccountingService.get_new_finance_trx_invoice(contragent_id, invoice_id),
                payer_promise = AccountingService.get_contragent_payer(contragent_id),
                invoice_promise = AccountingService.get_invoice(invoice_id);
            return $q.all([finance_trx_promise, payer_promise, invoice_promise])
                .then(function (data) {
                    var trxes = data[0],
                        payer = data[1],
                        invoice = data[2];
                    var instance = $modal.open({
                        templateUrl: '/WebMis20/modal/accounting/cashbook_invoice.html',
                        controller: CashbookInvoiceModalCtrl,
                        backdrop: 'static',
                        size: 'lg',
                        windowClass: 'modalScrollable',
                        resolve: {
                            payer: function () {
                                return payer;
                            },
                            trxes: function () {
                                return trxes;
                            },
                            invoice: function () {
                                return invoice;
                            }
                        }
                    });
                    return instance.result;
            });
        }
    }
}]);

WebMis20.service('AccountingService', ['WebMisApi', function (WebMisApi) {
    this.get_contract = function (contract_id, args) {
        return WebMisApi.contract.get(contract_id, args);
    };
    this.get_contract_list = function (args) {
        return WebMisApi.contract.get_list(args);
    };
    this.save_contract = function (contract) {
        var contract_id = contract.id;
        return WebMisApi.contract.save(contract_id, contract);
    };
    this.delete_contract = function (contract) {
        var contract_id = contract.id;
        return WebMisApi.contract.del(contract_id);
    };
    this.get_available_contracts = function (client_id, finance_id, event_set_date) {
        return WebMisApi.contract.get_available({
            client_id: client_id,
            finance_id: finance_id,
            event_set_date: event_set_date
        });
    };
    this.search_contragent = function (query, ca_type_code) {
        return WebMisApi.contragent.get_list({
            query: query,
            ca_type_code: ca_type_code
        });
    };
    this.search_payer = function (query) {
        return WebMisApi.contragent.search_payer({
            query: query
        });
    };
    this.get_contragent_payer = function (payer_id) {
        return WebMisApi.contragent.get_payer(payer_id);
    };
    this.get_new_contingent = function (args) {
        return WebMisApi.contingent.get(undefined, args);
    };
    this.get_pricelists = function (finance_id) {
        return WebMisApi.pricelist.get_list({
            finance_id: finance_id
        });
    };
    this.search_mis_action_services = function (query, client_id, contract_id) {
        return WebMisApi.service.search_mis_action_services({
            query: query,
            client_id: client_id,
            contract_id: contract_id
        });
    };
    this.get_service = function (service_id, args) {
        return WebMisApi.service.get(service_id, args);
    };
    this.save_service_list = function (event_id, service_list) {
        return WebMisApi.service.save_service_list({
            event_id: event_id,
            service_list: service_list
        });
    };
    this.delete_service = function (service) {
        return WebMisApi.service.del(service.id);
    };
    this.get_listed_services = function (event_id) {
        return WebMisApi.service.get_list(event_id);
    };
    this.refreshServiceSubservices = function (service) {
        return WebMisApi.service.refreshServiceSubservices(service);
    };
    this.getServiceActionTypePrices = function (contract_id) {
        return WebMisApi.service.get_service_at_price(contract_id);
    };
    this.get_invoice = function (invoice_id, args) {
        return WebMisApi.invoice.get(invoice_id, args);
    };
    this.save_invoice = function (invoice) {
        var invoice_id = invoice.id;
        return WebMisApi.invoice.save(invoice_id, invoice);
    };
    this.delete_invoice = function (invoice) {
        var invoice_id = invoice.id;
        return WebMisApi.invoice.del(invoice_id);
    };
    this.search_invoice = function (query, payer_id) {
        return WebMisApi.invoice.search({
            query: query,
            payer_id: payer_id
        });
    };
    this.get_new_finance_trx = function (contragent_id) {
        return WebMisApi.finance_trx.get_new({
            contragent_id: contragent_id
        });
    };
    this.make_finance_transaction = function (trx_type, args) {
        return WebMisApi.finance_trx.make_trx(trx_type.code, args);
    };
    this.get_new_finance_trx_invoice = function (contragent_id, invoice_id) {
        return WebMisApi.finance_trx.get_new_invoice_trxes({
            contragent_id: contragent_id,
            invoice_id: invoice_id
        });
    };
    this.make_finance_transaction_invoice = function (trx_type, args) {
        return WebMisApi.finance_trx.make_invoice_trx(trx_type.code, args);
    };
    this.get_service_discounts = function () {
        return WebMisApi.service_discount.get_list();
    };
    this.calc_service_sum = function (service, amount, discount) {
        return WebMisApi.service.calc_sum({
            service_id: service.service.id,
            price_list_item_id: service.service.price_list_item_id,
            amount: amount,
            discount_id: discount.id
        });
    };
    this.calc_invoice_sum = function (invoice) {
        return WebMisApi.invoice.calc_sum(invoice.id, invoice);
    };
}]);