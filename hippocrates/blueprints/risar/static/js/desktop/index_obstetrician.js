
var IndexObstetricianCtrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: undefined
    };
    $scope.query = "";
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.curYear = new Date().getFullYear();

    $scope.toolTipContent_pregnancy_week = function(){
        return function(key, x, y, e, graph) {
            return  '<h4>'+ x  + ' неделя'+ '</h4>'+ '<p>' +  y + '</p>'
        }
    };
    $scope.colorFunction = function() {
        return function(d, i) {
            if (d[0]<=14){
                return '#F493F2'
            } else if (14 < d[0] && d[0]<= 26){
                return '#E400E0'
            } else if (27 < d[0] && d[0]<= 40){
                return '#9600CD'
            } else {
                return '#5416B4';
            }
        };
    }
    $scope.yAxisTickFormat = function(d){
        return d;
    }
    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });
    $scope.current_stats = function(){
        RisarApi.current_stats.get().then(function (result) {
            $scope.current_stats = result;
        })
    };
    $scope.refresh_pregnancy_week_diagram = function (){
        RisarApi.pregnancy_week_diagram.get().then(function (result) {
            $scope.pregnancy_week = [{
                "key": "Пациентки по сроку беременности",
                "values": result
            }]
            $scope.pregnancy_week_all = result.reduce(function(prev, curr){
                        return prev + curr[1]
                    }, 0);
        })
    }
    $scope.load_need_hospitalization = function(){
        RisarApi.need_hospitalization.get().then(function (result) {
            $scope.need_hospitalization = result;
        });
    }

    $scope.current_stats();
    $scope.refresh_pregnancy_week_diagram();
    $scope.load_need_hospitalization();

};
WebMis20.controller('IndexObstetricianCtrl', ['$scope', 'RisarApi',
    IndexObstetricianCtrl]);