'use strict';

var ContractListCtrl = function ($scope, AccountingService, ContractModalService) {
    $scope.contract_list = [];
    $scope.pager = {
        current_page: 1,
        per_page: 15,
        max_pages: 10,
        pages: null,
        record_count: null
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
            per_page: $scope.pager.per_page
            //measure_type_id_list: $scope.query.measure_type.length ? _.pluck($scope.query.measure_type, 'id') : undefined,
            //beg_date_from: $scope.query.beg_date_from ? moment($scope.query.beg_date_from).startOf('day').toDate() : undefined,
            //beg_date_to: $scope.query.beg_date_to ? moment($scope.query.beg_date_to).endOf('day').toDate() : undefined,
            //end_date_from: $scope.query.end_date_from ? moment($scope.query.end_date_from).startOf('day').toDate() : undefined,
            //end_date_to: $scope.query.end_date_to ? moment($scope.query.end_date_to).endOf('day').toDate() : undefined,
            //measure_status_id_list: $scope.query.status.length ? _.pluck($scope.query.status, 'id') : undefined
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
    $scope.onPageChanged = function () {
        refreshContractList(true);
    };
    $scope.canEdit = function () {
        return true;
    };
    $scope.init = function () {
        refreshContractList();
    };

    $scope.init();
};

WebMis20.controller('ContractListCtrl', ['$scope', 'AccountingService', 'ContractModalService', ContractListCtrl]);
