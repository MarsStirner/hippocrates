/**
 * Created by mmalkov on 21.07.14.
 */

var EventListCtrl = function ($scope, $http, $window) {
    function get_model(page) {
        var model = {
            page: page
        };
        if ($scope.flt.id) model.id = $scope.flt.id;
        if ($scope.flt.external_id) model.external_id = $scope.flt.external_id;
        if ($scope.flt.client) model.client_id = $scope.flt.client.id;
        if ($scope.flt.beg_date) model.beg_date = moment($scope.flt.beg_date).format('YYYY-MM-DD');
        if ($scope.flt.end_date) model.end_date = moment($scope.flt.end_date).format('YYYY-MM-DD');
        if ($scope.flt.unfinished) model.unfinished = $scope.flt.unfinished;
        if ($scope.flt.finance_type) model.finance_id = $scope.flt.finance_type.id;
        if ($scope.flt.request_type) model.request_type_id = $scope.flt.request_type.id;
        if ($scope.flt.speciality) model.speciality_id = $scope.flt.speciality.id;
        if ($scope.flt.exec_person) model.exec_person_id = $scope.flt.exec_person.id;
        if ($scope.flt.result) model.result_id = $scope.flt.result.id;
        return model;
    }
    $scope.get_data = function (page) {
        var flt = get_model(page);
        if ($scope.current_sorting) {
            flt.sorting_params = $scope.current_sorting;
        }
        $http.post(url_event_api_get_events, flt)
        .success(function (data) {
            $scope.page = page;
            $scope.pages = data.result.pages;
            $scope.results = data.result.items;
            if (!$scope.current_sorting) {
                $scope.current_sorting = {
                    order: 'ASC',
                    column_name: 'beg_date'
                };
                var i,
                    columns = $scope.wmSortableHeaderCtrl.sort_cols;
                for (i = 0; i < columns.length; ++i) {
                    if (columns[i].column_name === 'beg_date') {
                        columns[i].order = 'ASC';
                        break;
                    }
                }
            }
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
            beg_date: moment().toDate(),
            end_date: null,
            finance_type: undefined,
            request_type: undefined,
            exec_person: null,
            unfinished: true
        };
        $scope.get_data();
    };
    $scope.on_unfinished_changed = function () {
        if ($scope.flt.unfinished) {
            $scope.flt.end_date = null;
        }
    };
    var sort_locally = function (col_name, order) {
        if (order === undefined) {
            col_name = 'beg_date';
            order = 'ASC';
        }

        $scope.results.sort(function (a, b) {
            if (a[col_name] < b[col_name]) {
                return order === 'ASC' ? -1 : 1;
            }
            if (a[col_name] > b[col_name]) {
                return order === 'DESC' ? -1 : 1;
            }
            return 0;
        });
    };
    $scope.sort_by_column = function (params) {
        var order = params.order,
            col_name = params.column_name;
        if (order === undefined) {
            $scope.current_sorting = undefined;
        } else {
            $scope.current_sorting = params;
        }
        if ($scope.pages === 1) {
            sort_locally(col_name, order);
        } else if ($scope.pages > 1) {
            $scope.get_data($scope.page);
        }
    };
    $scope.clear = function () {
        $scope.page = 1;
        $scope.pages = 1;
        $scope.flt = {
            id: null,
            external_id: undefined,
            client: undefined,
            beg_date: null,
            end_date: null,
            finance_type: undefined,
            request_type: undefined,
            speciality: undefined,
            exec_person: null,
            result: undefined,
            unfinished: false
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

    $scope.clients = [];
    $scope.last_query = '';
    $scope.max_size = 8;
    $scope.current_sorting = undefined;

    $scope.clear_all();
};
WebMis20.controller('EventListCtrl', ['$scope', '$http', '$window', EventListCtrl]);