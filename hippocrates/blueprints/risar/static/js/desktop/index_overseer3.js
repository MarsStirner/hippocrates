var IndexOverseer3Ctrl = function ($scope, RisarApi) {
    $scope.curation_level = {
        code: '3'
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
    $scope.refresh_gistograms();
};

WebMis20.controller('IndexOverseer3Ctrl', ['$scope', 'RisarApi',
    IndexOverseer3Ctrl]);
