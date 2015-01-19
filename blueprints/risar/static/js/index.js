/**
 * Created by mmalkov on 24.09.14.
 */
var IndexCtrl = function ($scope, RisarApi) {
    $scope.query = "";
    $scope.date = null;
    $scope.tickets = [];
    $scope.$watch('date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });
    // Подгрузки данных пока нет
    $scope.slices = [
        {
            key: 'Низкая',
            value: 50,
            color: '#30D040'
        },
        {
            key: 'Средняя',
            value: 200,
            color: '#E0C030'
        },
        {
            key: 'Высокая',
            value: 100,
            color: '#E05030'
        }
    ];
    $scope.slices_x = function () {
        return function (d) {
            return d.key;
        }
    };
    $scope.slices_y = function () {
        return function (d) {
            return d.value;
        }
    };
    $scope.slices_c = function () {
        return function (d, i) {
            // А это, ребятки, костыль, потому что где-то в d3 или nv - багулечка
            return d.data.color;
        }
    };
    $scope.date = new Date();
    $scope.declOfNum = function (number, titles){
        if (number == undefined){
            number = 0;
        }
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    }
};
