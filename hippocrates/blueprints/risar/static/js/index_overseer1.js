var IndexOverseer1Ctrl = function ($scope, RisarApi) {
    $scope.query = "";
    $scope.search_date = {date:new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];
    $scope.curYear = new Date().getFullYear();
    $scope.chart_fill_assessment = [{
        "key": "Series 1",
        "values": [['Трунова Н.С.', 25], ['Папуша Л.А.', 18], ['Мамзерова П.Р.', 15], ['Семенова В.Ф.', 11], ['Горячева Л.Л.', 7]]
    }]

    $scope.xAxisTickFormat = function(d){
        var m = moment();
        return m.months(d-1).format('MMM');
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
        RisarApi.prenatal_risk_stats.get().then(function (result) {
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
                    color: '#f39c12'
                })
            }
            if (result['3']) {
                $scope.slices.push({
                    key: 'Высокая',
                    value: result['3'],
                    color: '#dd4b39'
                })
            }
        })
    };

    $scope.refresh_diagram();
};

WebMis20.controller('IndexOverseer1Ctrl', ['$scope', 'RisarApi',
    IndexOverseer1Ctrl]);