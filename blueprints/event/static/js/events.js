/**
 * Created by mmalkov on 21.07.14.
 */

var EventListCtrl = function ($scope, $http) {
    function get_model(page) {
        var model = {
            page: page
        };
        if ($scope.flt.id) model.id = $scope.flt.id;
        if ($scope.flt.client) model.client_id = $scope.flt.client.id;
        if ($scope.flt.exec_person) model.exec_person_id = $scope.flt.exec_person.id;
        if ($scope.flt.beg_date) model.beg_date = moment($scope.flt.beg_date).format('YYYY-MM-DD');
        if ($scope.flt.end_date) model.end_date = moment($scope.flt.end_date).format('YYYY-MM-DD');
        if ($scope.flt.unfinished) model.unfinished = $scope.flt.unfinished;
        if ($scope.flt.finance_type) model.finance_id = $scope.flt.finance_type.id;
        if ($scope.flt.request_type) model.request_type_id = $scope.flt.request_type.id;
        return model;
    }
    $scope.get_data = function (page) {
        $http.post(url_event_api_get_events, get_model(page))
        .success(function (data) {
            $scope.page = page;
            $scope.pages = data.result.pages;
            $scope.results = data.result.items;
        })
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
    $scope.clear = function () {
        $scope.page = 1;
        $scope.pages = 1;
        $scope.flt = {
            id: null,
            client: undefined,
            beg_date: null,
            end_date: null,
            finance_type: undefined,
            request_type: undefined,
            exec_person: null,
            unfinished: false
        };
    };
    $scope.clear_all = function () {
        $scope.clear();
        $scope.results = [];
    };

    $scope.url_event_get = url_for_event_html_event_info;
    $scope.url_client_get = url_client_html;

    $scope.clients = [];
    $scope.last_query = '';
    $scope.max_size = 8;

    $scope.clear_all();
};
WebMis20.controller('EventListCtrl', ['$scope', '$http', EventListCtrl]);