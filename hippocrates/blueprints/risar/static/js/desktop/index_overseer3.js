
var IndexOverseer3Ctrl = function ($controller, $scope, RisarApi) {
    $scope.curation_level = {
        code: '3'
    };
    $scope.query = {
        client: undefined,
        search_str: undefined
    };
    $scope.search_date = {date: new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];

    $controller('BaseDeathDateStatCtrl', {$scope: $scope});

    $scope.onQuickSearchChanged = function () {
        // used in ui-select with ext-select-quick-event-search
        return function (query_str) {
            $scope.query.search_str = query_str;
        }
    };

    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule.get_appointments(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });
};

WebMis20.controller('IndexOverseer3Ctrl', ['$controller', '$scope', 'RisarApi',
    IndexOverseer3Ctrl]);
