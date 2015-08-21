var IndexOverseer2Ctrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: '2'
    };
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
    $scope.pager_recently_modified_charts = {
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
    $scope.current_stats = function(){
        RisarApi.current_stats.get(2).then(function (result) {
            $scope.current_stats = result;
        })
    };

    $scope.refresh_pregnancy_week_diagram = function (){
        RisarApi.pregnancy_week_diagram.get(2).then(function (result) {
            $scope.pregnancy_week = [{
                "key": "Пациентки по сроку беременности",
                "values": result
            }]
            $scope.pregnancy_week_all = result.reduce(function(prev, curr){
                        return prev + curr[1]
                    }, 0);
        })
    }
    var recently_modified_charts = function() {
        var data = {
            per_page: $scope.itemsPerPage,
            page: $scope.pager_recently_modified_charts.current_page,
            curation_level: 1,
            risk_rate:[3]
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
    $scope.current_stats();
    recently_modified_charts();
    $scope.refresh_pregnancy_week_diagram();
};

WebMis20.controller('IndexOverseer2Ctrl', ['$scope', 'RisarApi',
    IndexOverseer2Ctrl]);