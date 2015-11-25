'use strict';

WebMis20.service('ContractModalService', ['$modal', function ($modal) {
    return {
        openEdit: function (contract) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal/contract_edit.html',
                controller: ContractModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    contract: function () {
                        return contract
                    }
                }
            });
            return instance.result;
        }
    }
}]);

WebMis20.service('AccountingService', ['WebMisApi', function (WebMisApi) {
    this.get_contract = function (contract_id) {
        return WebMisApi.contract.get(contract_id);
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
    this.get_new_contingent = function (args) {
        return WebMisApi.contingent.get(undefined, args);
    };
    this.get_pricelists = function (finance_id) {
        return WebMisApi.pricelist.get_list({
            finance_id: finance_id
        });
    };
}]);