/**
 * Created by mmalkov on 21.07.14.
 */

var EventListCtrl = function ($scope, $http, $window, $q, MessageBox) {
    function get_model(page) {
        var model = {
            page: page
        };
        if ($scope.flt.id) model.id = $scope.flt.id;
        if ($scope.flt.external_id) model.external_id = $scope.flt.external_id;
        if ($scope.flt.client) model.client_id = $scope.flt.client.id;
        if ($scope.flt.beg_date_from) model.beg_date_from = moment($scope.flt.beg_date_from).startOf('day').toDate();
        if ($scope.flt.beg_date_to) model.beg_date_to = moment($scope.flt.beg_date_to).endOf('day').toDate();
        if ($scope.flt.end_date_from) model.end_date_from = moment($scope.flt.end_date_from).startOf('day').toDate();
        if ($scope.flt.end_date_to) model.end_date_to = moment($scope.flt.end_date_to).endOf('day').toDate();
        if ($scope.flt.unfinished) model.unfinished = $scope.flt.unfinished;
        if ($scope.flt.finance_type) model.finance_id = $scope.flt.finance_type.id;
        if ($scope.flt.request_type) model.request_type_id = $scope.flt.request_type.id;
        if ($scope.flt.speciality) model.speciality_id = $scope.flt.speciality.id;
        if ($scope.flt.exec_person) model.exec_person_id = $scope.flt.exec_person.id;
        if ($scope.flt.result) model.result_id = $scope.flt.result.id;
        if ($scope.flt.org_struct) model.org_struct_id = $scope.flt.org_struct.id;
        if ($scope.flt.diag_mkb) model.diag_mkb = $scope.flt.diag_mkb;
        if ($scope.flt.draft_contract) model.draft_contract = $scope.flt.draft_contract;
        return model;
    }

    var current_monday = moment().startOf('week').toDate();

    var checkSearchParams = function (flt) {
        var deferred = $q.defer();
        if (flt.org_struct_id && !(flt.beg_date_from || flt.end_date_from)) {
            return MessageBox.error(
                'Укажите диапазон дат для поиска',
                'При выборе отделения для поиска обращений необходимо также указать дату начала и завершения'
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
                $http.post(url_event_api_get_events, flt)
                    .success(function (data) {
                        $scope.page = page;
                        $scope.pages = data.result.pages;
                        $scope.results = data.result.items;
                        $scope.total = data.result.total;
                        if (!$scope.current_sorting) {
                            $scope.reset_sorting();
                        }
                    });
            });
    };
    $scope.get_clients = function (query) {
        if (!query) return;
        return $http.get(url_client_search, {
            params: {
                q: query,
                short: true,
                limit: 20
            }
        })
        .then(function (res) {
            return $scope.clients = res.data.result;
        });
    };
    $scope.diurnal = function () {
        $scope.flt = {
            id: null,
            external_id: undefined,
            client: undefined,
            beg_date_from: moment().startOf('day').toDate(),
            beg_date_to: moment().endOf('day').toDate(),
            finance_type: undefined,
            request_type: undefined,
            exec_person: null,
            unfinished: true
        };
        $scope.reset_sorting();
        $scope.get_data();
    };
    $scope.on_unfinished_changed = function () {
        if ($scope.flt.unfinished) {
            $scope.flt.end_date_from = null;
            $scope.flt.end_date_to = null;
        }
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
            external_id: undefined,
            client: undefined,
            beg_date_from: current_monday,
            beg_date_to: null,
            end_date_from: null,
            end_date_to: null,
            finance_type: undefined,
            request_type: undefined,
            speciality: undefined,
            exec_person: null,
            result: undefined,
            org_struct: null,
            diag_mkb: null,
            unfinished: false,
            draft_contract: false
        };
    };
    $scope.clear_all = function () {
        $scope.clear();
        $scope.results = [];
    };
    $scope.open_event = function (event_id) {
        $window.open(url_for_event_html_event_info + '?event_id=' + event_id);
    };
    $scope.rbResultFormatter = function (selected) {
        return selected ? '{0} ({1})'.format(selected.name, selected.event_purpose.name) : undefined;
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

    $scope.clients = [];
    $scope.last_query = '';
    $scope.max_size = 8;
    $scope.current_sorting = undefined;

    $scope.clear_all();
};
WebMis20.controller('EventListCtrl', ['$scope', '$http', '$window', '$q', 'MessageBox', EventListCtrl]);