var IndexOverseer1Ctrl = function ($scope, RisarApi) {
    $scope.query = "";
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
    $scope.chart_fill_assessment = [{
        "key": "Series 1",
        "values": [['Трунова Н.С.', 25], ['Папуша Л.А.', 18], ['Мамзерова П.Р.', 15], ['Семенова В.Ф.', 11], ['Горячева Л.Л.', 7]],
        "color": '#dd4b39'
    }]

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
    $scope.current_stats = function(){
        RisarApi.current_stats.get(1).then(function (result) {
            $scope.current_stats = result;
        })
    };

    var recent_charts = function() {
        var data = {
            per_page: $scope.itemsPerPage,
            page: $scope.pager.current_page,
            curation_level: 1
        }
        RisarApi.recent_charts.get(data).then(function (result) {
            $scope.pager.pages = result.total_pages;
            $scope.pager.record_count = result.count;
            $scope.recent_charts = result.events;
        })
    };
    $scope.onPageChanged = function () {
        recent_charts();
    };
    $scope.refresh_diagram = function () {
        RisarApi.prenatal_risk_stats.get(1).then(function (result) {
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
    $scope.refresh_pregnancy_week_diagram = function (){
        RisarApi.pregnancy_week_diagram.get(1).then(function (result) {
            $scope.pregnancy_week = [{
                "key": "Пациентки по сроку беременности",
                "values": result
            }]
            $scope.pregnancy_week_all = result.reduce(function(prev, curr){
                        return prev + curr[1]
                    }, 0);
        })
    }
    $scope.current_stats();
    recent_charts();
    $scope.refresh_diagram();
    $scope.refresh_pregnancy_week_diagram();
};

WebMis20.controller('IndexOverseer1Ctrl', ['$scope', 'RisarApi',
    IndexOverseer1Ctrl]);