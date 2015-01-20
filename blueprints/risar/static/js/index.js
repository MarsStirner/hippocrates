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
            value: 0,
            color: '#30D040'
        },
        {
            key: 'Средняя',
            value: 0,
            color: '#E0C030'
        },
        {
            key: 'Высокая',
            value: 0,
            color: '#E05030'
        }
    ];
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
            if (result['низкая']) {
                $scope.slices.push({
                    key: 'Низкая',
                    value: result['низкая'],
                    color: '#30D040'
                })
            }
            if (result['средняя']) {
                $scope.slices.push({
                    key: 'Средняя',
                    value: result['средняя'],
                    color: '#E0C030'
                })
            }
            if (result['высокая']) {
                $scope.slices.push({
                    key: 'Высокая',
                    value: result['высокая'],
                    color: '#E05030'
                })
            }
        })
    };
    $scope.refresh_diagram();
    $scope.date = new Date();
    $scope.declOfNum = function (number, titles){
        if (number == undefined){
            number = 0;
        }
        var cases = [2, 0, 1, 1, 1, 2];
        return titles[ (number%100>4 && number%100<20)? 2 : cases[(number%10<5)?number%10:5] ];
    }
};
