var IndexOverseer2Ctrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: '2'
    };
    $scope.query = {
        client: undefined,
        search_str: undefined
    };
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.curYear = new Date().getFullYear();
    $scope.itemsPerPage = 5;
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1,
        record_count: 0
    };
    $scope.pager_recently_modified_charts = {
        current_page: 1,
        max_pages: 10,
        pages: 1,
        record_count: 0
    };

    $scope.onQuickSearchChanged = function () {
        // used in ui-select with ext-select-quick-event-search
        return function (query_str) {
            $scope.query.search_str = query_str;
        }
    };
    $scope.xAxisTickFormat = function(d){
        var m = moment();
        return m.months(d-1).format('MMM');
    }
    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });

    var recently_modified_charts = function() {
        var data = {
            per_page: $scope.itemsPerPage,
            page: $scope.pager_recently_modified_charts.current_page,
            curation_level: 1,
            risk_rate:[4] //high
        }
        RisarApi.recently_modified_charts.get(data).then(function (result) {
            $scope.pager_recently_modified_charts.pages = result.total_pages;
            $scope.pager_recently_modified_charts.record_count = result.count;
            $scope.recently_modified_charts = result.events;
        })
    };
    $scope.onRecentlyModifiedPageChanged = function () {
        recently_modified_charts();
    };
    recently_modified_charts();
};

WebMis20.controller('IndexOverseer2Ctrl', ['$scope', 'RisarApi',
    IndexOverseer2Ctrl]);