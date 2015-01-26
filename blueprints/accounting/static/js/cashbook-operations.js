'use strict';

var CashBookOperationsCtrl = function ($scope, $http, $window, RefBookService, PrintingService) {
    function get_model(page) {
        var model = {
            page: page
        };
        if ($scope.flt.beg_date) model.beg_date = aux.format_date($scope.flt.beg_date);
        if ($scope.flt.end_date) model.end_date = aux.format_date($scope.flt.end_date);
        if ($scope.flt.cashbox) model.cashbox = $scope.flt.cashbox;
        if ($scope.flt.cashier_person) model.cashier_person_id = $scope.flt.cashier_person.id;
        if ($scope.flt.payment_type) model.payment_type_id = $scope.flt.payment_type.id;
        if ($scope.flt.cash_operation) model.cash_operation_id = $scope.flt.cash_operation.id;
        if ($scope.flt.event_purpose) model.event_purpose_id = $scope.flt.event_purpose.id;
        if ($scope.flt.event_type) model.event_type_id = $scope.flt.event_type.id;
        if ($scope.flt.org_struct) model.org_struct_id = $scope.flt.org_struct.id;
        if ($scope.flt.exec_person) model.exec_person_id = $scope.flt.exec_person.id;
        return model;
    }

    $scope.max_size = 8;
    $scope.current_sorting = undefined;
    $scope.rbPaymentType = new RefBookService.get('PaymentType');
    $scope.ps = new PrintingService('');

    $scope.get_data = function (page, reset_sorting) {
        var flt = get_model(page);
        if (reset_sorting) {
            $scope.reset_sorting();
        }
        if ($scope.current_sorting) {
            flt.sorting_params = $scope.current_sorting;
        }
        $http.post(url_api_get_event_payments, flt)
        .success(function (data) {
            $scope.page = page;
            $scope.pages = data.result.pages;
            $scope.results = data.result.items;
            $scope.metrics = data.result.metrics;
            if (!$scope.current_sorting) {
                $scope.reset_sorting();
            }
        });
    };
    $scope.sort_by_column = function (params) {
        $scope.current_sorting = params;
        $scope.get_data($scope.page);
    };
    $scope.clear = function () {
        $scope.page = 1;
        $scope.pages = 1;
        $scope.flt = {
            beg_date: new Date(),
            end_date: new Date(),
            cashbox: null,
            cashier_person: null,
            payment_type: null,
            cash_operation: null,
            event_purpose: null,
            event_type: null,
            org_struct: null,
            exec_person: null
        };
    };
    $scope.clear_all = function () {
        $scope.clear();
        $scope.results = [];
    };
    $scope.open_event = function (event_id) {
        $window.open(url_for_event_html_event_info + '?event_id=' + event_id);
    };
    $scope.reset_sorting = function () {
        $scope.current_sorting = {
            order: 'DESC',
            column_name: 'date'
        };
        var i,
            columns = $scope.wmSortableHeaderCtrl.sort_cols;
        for (i = 0; i < columns.length; ++i) {
            if (columns[i].column_name === 'date') {
                columns[i].order = 'DESC';
            } else {
                columns[i].order = undefined;
            }
        }
    };

    $scope.clear_all();
};
WebMis20.controller('CashBookOperationsCtrl', ['$scope', '$http', '$window', 'RefBookService', 'PrintingService',
    CashBookOperationsCtrl]);