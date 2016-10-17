'use strict';

var ActionListCtrl = function ($scope, $q, $window, WebMisApi, MessageBox, WMConfig, CurrentUser) {
    $scope.last_query = '';
    $scope.max_size = 8;
    $scope.current_sorting = undefined;

    var get_model = function (page) {
        var model = {
            page: page
        };
        if ($scope.flt.id) model.id = $scope.flt.id;
        if ($scope.flt.status) model.status_id = $scope.flt.status.id;
        if ($scope.flt.client) model.client_id = $scope.flt.client.id;
        if ($scope.flt.action_type.length) model.action_type_id_list = _.pluck($scope.flt.action_type, 'id');
        if ($scope.flt.beg_date_from) model.beg_date_from = moment($scope.flt.beg_date_from).startOf('day').toDate();
        if ($scope.flt.beg_date_to) model.beg_date_to = moment($scope.flt.beg_date_to).endOf('day').toDate();
        if ($scope.flt.ped_from) model.ped_from = moment($scope.flt.ped_from).startOf('day').toDate();
        if ($scope.flt.ped_to) model.ped_to = moment($scope.flt.ped_to).endOf('day').toDate();
        if ($scope.flt.set_person) model.set_person_id = $scope.flt.set_person.id;
        if ($scope.flt.person) model.person_id = $scope.flt.person.id;
        if ($scope.flt.person_org_struct) model.person_org_structure_id = $scope.flt.person_org_struct.id;
        return model;
    };
    var current_monday = moment().startOf('week').toDate(),
        current_user_os = CurrentUser.info.org_structure;

    var checkSearchParams = function (flt) {
        var deferred = $q.defer();
        if (!['beg_date_from', 'beg_date_to', 'ped_from', 'ped_to', 'client'].some(function (param) {
            return Boolean($scope.flt[param]);
        })) {
            return MessageBox.error(
                'Укажите обязательные параметры фильтрации',
                'Для проведения поиска необходимо указать интересующий диапазон дат или выбрать пациента'
            );
        }
        deferred.resolve();
        return deferred.promise;
    };
    $scope.get_data = function (page, reset_sorting) {
        var flt = get_model(page);
        checkSearchParams(flt)
            .then(function () {
                if (reset_sorting) {
                    $scope.reset_sorting();
                }
                if ($scope.current_sorting) {
                    flt.sorting_params = $scope.current_sorting;
                }
                WebMisApi.action.search(flt)
                    .then(function (result) {
                        $scope.page = page;
                        $scope.pages = result.pages;
                        $scope.results = result.items;
                        $scope.total = result.total;
                        if (!$scope.current_sorting) {
                            $scope.reset_sorting();
                        }
                    });
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
            id: null,
            status: null,
            client: null,
            action_type: [],
            beg_date_from: current_monday,
            beg_date_to: null,
            ped_from: null,
            ped_to: null,
            set_person: null,
            person: null,
            person_org_struct: current_user_os
        };
    };
    $scope.clear_all = function () {
        $scope.clear();
        $scope.results = [];
    };
    $scope.reset_sorting = function () {
        $scope.current_sorting = {
            order: 'DESC',
            column_name: 'beg_date'
        };
        var i,
            columns = $scope.wmSortableHeaderCtrl.sort_cols;
        for (i = 0; i < columns.length; ++i) {
            if (columns[i].column_name === 'beg_date') {
                columns[i].order = 'DESC';
            } else {
                columns[i].order = undefined;
            }
        }
    };
    $scope.openAction = function (action_id) {
        $window.open(WMConfig.url.actions.html.action + '?action_id=' + action_id);
    };
    $scope.atFilter = function (item) {
        return item.hidden === 0;
    };

    $scope.clear_all();
};

WebMis20.controller('ActionListCtrl', ['$scope', '$q', '$window', 'WebMisApi', 'MessageBox',
    'WMConfig', 'CurrentUser', ActionListCtrl]);