/**
 * Created by mmalkov on 24.09.14.
 */
var IndexCtrl = function ($scope, RisarApi) {
    $scope.query = "";
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.infants_death = [
                  {
                      "key": "Умершие",
                      "values": [ [ 1, 10] , [ 2, 12] ],
                      "color": "#6699CC"
                  },
                  {
                      "key": "Живые",
                      "values": [ [ 3, 34] , [ 4, 38]],
                      "color": "#FF6633"
                  }
             ];

    $scope.pregnancy_results = [
                  {
                      "key": "Количество абортов",
                      "values": [ [ 1, 61] ],
                      "color": "#6699CC"
                  },
                  {
                      "key": "Количество родов",
                      "values": [ [ 2, 1234] ],
                      "color": "#FF6633"
                  }

    ];
    $scope.toolTipContentFunction_infants_death = function(){
        return function(key, x, y, e, graph) {
            var month = x%2 ? ' за ' + moment().add(-1, 'month').format("MMMM"): ' за ' + moment().format("MMMM");
            return  key + month + '<p>' +  y + '</p>'
        }
    }
    $scope.toolTipContentFunction_pregnancy_results = function(){
        return function(key, x, y, e, graph) {
            return  key + '<p>' +  y + '</p>'
        }
    }
    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });
    // Подгрузки данных пока нет
    $scope.slices = [];
    $scope.slices_x = function (d) {
        return d.key;
    };
    $scope.slices_y = function (d) {
        return d.value;
    };
    $scope.slices_c = function (d, i) {
        // А это, ребятки, костыль, потому что где-то в d3 или nv - багулечка
        return d.data.color;
    };
    $scope.refresh_diagram = function () {
        RisarApi.current_stats.get().then(function (result) {
            $scope.slices = [];
            if (result['0']) {
                $scope.slices.push({
                    key: 'Не определена',
                    value: result['0'],
                    color: '#707070'
                })
            }
            if (result['1']) {
                $scope.slices.push({
                    key: 'Низкая',
                    value: result['1'],
                    color: '#30D040'
                })
            }
            if (result['2']) {
                $scope.slices.push({
                    key: 'Средняя',
                    value: result['2'],
                    color: '#E0C030'
                })
            }
            if (result['3']) {
                $scope.slices.push({
                    key: 'Высокая',
                    value: result['3'],
                    color: '#E05030'
                })
            }
        })
    };
    $scope.refresh_diagram();
    $scope.declOfNum = function (number, titles){
        if (number == undefined){
            number = 0;
        }
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    }
};
