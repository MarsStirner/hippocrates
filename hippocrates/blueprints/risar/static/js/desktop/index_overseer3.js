var IndexOverseer3Ctrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: '3'
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
            } else if (27 <= d[0] && d[0]<= 40){
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
    $scope.xAxisTickFormatYears = function(d){
        if (d%1 ===0){
            return d;
        }
    }
    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });

    $scope.refresh_gistograms = function () {
        RisarApi.death_stats.get().then(function (result) {
            // 0 - dead, 1 - alive
            $scope.infants_prev_years = [];
            if (result){
                var result_current_year = result[0];
                var prev_years_perinatal_death = result[1];
                var prev_years_birth = result[2];
                var prev_years_maternal_death = result[3];

                var dead = result_current_year['0'].reduce(function(sum, current){
                    return sum + current[1];
                }, 0);
                var alive = result_current_year['1'].reduce(function(sum, current){
                    return sum + current[1];
                }, 0);
                var maternal_death_all = result_current_year['maternal_death'].reduce(function(sum, current){
                    return sum + current[1];
                }, 0);
                $scope.infants_death_coeff = (dead/(dead + alive)*1000).toFixed(2);
                $scope.maternal_death_coeff = (maternal_death_all/alive*100000).toFixed(2);
                $scope.infants_death = [
                              {
                                  "key": "Количество умерших детей",
                                  "values": result_current_year['0'],
                                  "color": "#FF6633"
                              },
                              {
                                  "key": "Количество живых детей",
                                  "values": result_current_year['1'],
                                  "color": "#339933"
                              }
                         ];
                $scope.maternal_death = [
                              {
                                  "key": "Количество умерших пациенток",
                                  "values": result_current_year['maternal_death'],
                                  "color": "#FF6633"
                              }
                         ];
                for (var key in prev_years_perinatal_death){
                    if (prev_years_perinatal_death[key].length){
                        var color = key == 'РФ' ? "#FF9728": "#FF6633";
                        $scope.infants_prev_years.push({
                            "key": key+', смертность',
                            "values": prev_years_perinatal_death[key],
                            "color": color
                            })
                    }

                }
                for (var key in prev_years_birth){
                    if (prev_years_birth[key].length){
                        var color = key == 'РФ' ? "#3c8dbc": "#339933";
                        $scope.infants_prev_years.push({
                            "key": key+', рождаемость',
                            "values": prev_years_birth[key],
                            "color": color
                            })
                    }

                }
                $scope.prev_years_maternal_death = [];
                for (var key in prev_years_maternal_death){
                    if (prev_years_maternal_death[key].length){
                        var color = key == 'РФ' ? "#FF9728": "#FF6633";
                        $scope.prev_years_maternal_death.push({
                            "key": key,
                            "values": prev_years_maternal_death[key],
                            "color": color
                            })
                    }

                }
            } else{
                $scope.infants_death = [];
                $scope.maternal_death = [];
            }
        });
    };
    $scope.refresh_pregnancy_week_diagram = function (){
        RisarApi.pregnancy_week_diagram.get(3).then(function (result) {
            $scope.pregnancy_week = [{
                "key": "Пациентки по сроку беременности",
                "values": result
            }]
            $scope.pregnancy_week_all = result.reduce(function(prev, curr){
                        return prev + curr[1]
                    }, 0);
        })
    }
    $scope.refresh_gistograms();
    $scope.refresh_pregnancy_week_diagram();
};

WebMis20.controller('IndexOverseer3Ctrl', ['$scope', 'RisarApi',
    IndexOverseer3Ctrl]);
