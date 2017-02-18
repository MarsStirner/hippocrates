
var IndexObstetricianCtrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: undefined
    };
    $scope.query = {
        client: undefined,
        search_str: undefined
    };
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.curYear = new Date().getFullYear();

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
    $scope.load_need_hospitalization = function(){
        RisarApi.need_hospitalization.get().then(function (result) {
            $scope.need_hospitalization = result;
        });
    }
    $scope.load_need_hospitalization();

};
WebMis20.controller('IndexObstetricianCtrl', ['$scope', 'RisarApi',
    IndexObstetricianCtrl]);