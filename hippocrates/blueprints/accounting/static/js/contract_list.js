'use strict';

var ContractListCtrl = function ($scope, AccountingService, ContractModalService, MessageBox) {
    $scope.contract_list = [];
    $scope.pager = {
        current_page: 1,
        per_page: 15,
        max_pages: 10,
        pages: null,
        record_count: null
    };
    $scope.flt = {
        enabled: false,
        model: {}
    };

    var setContractListData = function (paged_data) {
        $scope.contract_list = paged_data.contract_list;
        $scope.pager.record_count = paged_data.count;
        $scope.pager.pages = paged_data.total_pages;
    };
    var refreshContractList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var args = {
            paginate: true,
            page: $scope.pager.current_page,
            per_page: $scope.pager.per_page,
            number: $scope.flt.model.number || undefined,
            finance_id: safe_traverse($scope.flt.model, ['finance_type', 'id']),
            payer_query: $scope.flt.model.payer_query || undefined,
            recipient_query: $scope.flt.model.recipient_query || undefined,
            beg_date_from: $scope.flt.model.beg_date_from || undefined,
            beg_date_to: $scope.flt.model.beg_date_to || undefined,
            end_date_from: $scope.flt.model.end_date_from || undefined,
            end_date_to: $scope.flt.model.end_date_to || undefined,
            set_date_from: $scope.flt.model.set_date_from || undefined,
            set_date_to: $scope.flt.model.set_date_to || undefined
        };
        AccountingService.get_contract_list(args).then(setContractListData);
    };
    $scope.create = function () {
        AccountingService.get_contract()
            .then(function (contract) {
                return ContractModalService.openEdit(contract);
            })
            .then(function (result) {
                var contract = result.contract;
                $scope.contract_list.push(contract);
            });
    };
    $scope.editContract = function (idx) {
        var contract = _.deepCopy($scope.contract_list[idx]);
        ContractModalService.openEdit(contract)
            .then(function (result) {
                var upd_contract = result.contract;
                $scope.contract_list.splice(idx, 1, upd_contract);
            });
    };
    $scope.deleteContract = function (idx) {
        var contract = $scope.contract_list[idx];
        MessageBox.question(
            'Удаление договора',
            'Вы уверены, что хотите удалить выбранный договор?'
        ).then(function () {
            AccountingService.delete_contract(contract)
                .then(function () {
                    $scope.contract_list.splice(idx, 1);
                });
        });
    };
    $scope.onPageChanged = function () {
        refreshContractList(true);
    };
    $scope.canEdit = function () {
        return true;
    };
    $scope.canDelete = function () {
        return true;
    };
    $scope.toggleFilter = function () {
        $scope.flt.enabled = !$scope.flt.enabled;
    };
    $scope.isFilterEnabled = function () {
        return $scope.flt.enabled;
    };
    $scope.clear = function () {
        $scope.pager.current_page = 1;
        $scope.pager.pages = null;
        $scope.pager.record_count = null;
        $scope.flt.model = {};
    };
    $scope.clearAll = function () {
        $scope.clear();
        $scope.contract_list = [];
    };
    $scope.getData = function () {
        refreshContractList();
    };

    $scope.init = function () {
        refreshContractList();
    };

    $scope.init();
};

WebMis20.controller('ContractListCtrl', ['$scope', 'AccountingService', 'ContractModalService',
    'MessageBox', ContractListCtrl]);
