
var IndexObstetricianCtrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: undefined
    };
    $scope.query = "";
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.curYear = new Date().getFullYear();

    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
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