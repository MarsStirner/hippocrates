WebMis20.controller('BaseDeathDateStatCtrl', ['$scope', 'RisarApi', function ($scope, RisarApi) {
    $scope.refresh_gistograms_by_period = function () {
        return
    };
    $scope.$on('elementClick.directive', function (angularEvent, event) {
        $scope.$apply(function () {
            console.log(event);
            $scope.selected_point_x = event.pointIndex;
        });
    });
    $scope.curDate = new Date();
    $scope.curYear = $scope.curDate.getFullYear();
    $scope.dt = {'start_date': undefined, 'end_date': undefined};
    $scope.dt['start_date'] = moment($scope.curDate).clone().add(-6, 'd').toDate();
    $scope.dt['max_start_date'] = moment($scope.curDate).clone().add(-1, 'd').toDate();
    $scope.dt['end_date'] = moment($scope.curDate).clone().toDate();
    $scope.check_start_date = function (momented) {
        $scope.dt['start_date'] = momented.clone().add(-1, 'd').toDate();
    };
    $scope.$watch('dt.start_date', function (n, o) {
        if (n && n !== o) {
            var momented = moment(n);
            if (momented.toDate() >= moment($scope.dt['end_date']).toDate()) {
                $scope.check_start_date(momented)
            } else {
                $scope.refresh_gistograms_by_period();
            }
        }
    });
    $scope.$watch('dt.end_date', function (n, o) {
        if (n && n !== o) {
            var momented = moment(n);
            if (momented.toDate() <= moment($scope.dt['start_date']).toDate()) {
                $scope.check_start_date(momented);
            } else {
                $scope.refresh_gistograms_by_period();
            }
        }
    });


    //all below may vary between descendant controllers
    //just override
    $scope.xAxisTickFormat = function (d) {
        if (d % 1 === 0) {
            //целое число
            if (angular.isDefined($scope.dt_range)) {
                var x_date = moment.unix($scope.dt_range[d - 1]).format('DD.MM.YYYY');
                return x_date;
            }
        }
    };
    $scope.xAxisTickFormatYears = function (d) {
        if (d % 1 === 0) {
            return d;
        }
    };
    $scope._makeLegend = function (nameOnScope, keyValueObject, colorIfRF, colorIfnotRF, label) {
        $scope[nameOnScope] = [];
        for (var key in keyValueObject) {
            if (keyValueObject[key].length) {
                var color = key == 'РФ' ? colorIfRF : colorIfnotRF;
                // var color = key == 'РФ' ? "#FF9728": "#FF6633";
                $scope[nameOnScope].push({
                    "key": label ? key + label : key,
                    "values": keyValueObject[key],
                    "color": color
                })
            }
        }
    };

}]);

WebMis20.controller('MaternalDeathStatCtrl', ['$controller', '$scope', 'RisarApi', function ($controller, $scope, RisarApi) {
    $controller('BaseDeathDateStatCtrl', {$scope: $scope});

    $scope.selected_point_x = undefined;
    $scope.closeChosenCards = function () {
        $scope.selected_point_x = undefined;
    };

    $scope.refresh_gistograms_by_period = function () {
        RisarApi.maternal_death_stats.get_period($scope.dt.start_date, $scope.dt.end_date).then(function (result) {
            $scope.maternal_death = [];
            $scope.prev_years_maternal_death = [];
            if (result) {
                var prev_years_maternal_death = result["prev_years_maternal_death"];
                $scope.dt_range = result["dt_range"];
                $scope.maternal_cards_info = result["maternal_cards_info"];
                $scope.maternal_death_coeff = result["maternal_death_coeff"].toFixed(2);
                $scope.maternal_death.push(
                    {
                        "key": "Количество умерших пациенток",
                        "values": result['maternal_death'],
                        "color": "#FF6633"
                    }
                );
                for (var key in prev_years_maternal_death) {
                    if (prev_years_maternal_death[key].length) {
                        var color = key == 'РФ' ? "#FF9728" : "#FF6633";
                        $scope.prev_years_maternal_death.push({
                            "key": key,
                            "values": prev_years_maternal_death[key],
                            "color": color
                        })
                    }
                }
            }
        });
    };
    $scope.refresh_gistograms_by_period();
}]);

WebMis20.controller('PerinatalDeathStatCtrl', ['$controller', '$scope', 'RisarApi', function ($controller, $scope, RisarApi) {
    $controller('BaseDeathDateStatCtrl', {$scope: $scope});
    $scope.selected_point_x = null;
    $scope.alive_children_cards = [];
    $scope.has_dead_value = [];
    $scope.$watch('selected_point_x', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.alive_children_cards = $scope.alive_children_cards_info[newValue];
            $scope.dead_children_cards = $scope.dead_children_cards_info[newValue];
        }
    });
    
    $scope.refresh_gistograms_by_period = function () {
        //todo: ^should be another separate url
        RisarApi.perinatal_death_stats.get_period($scope.dt.start_date, $scope.dt.end_date).then(function (result) {
            $scope.infants_prev_years = [];
            $scope.infants_death = [];
            $scope.dt_range = result["dt_range"];
            $scope.selected_point_x = null;
            if (result) {
                var prev_years_perinatal_death = result['prev_years_perinatal_death'],
                    prev_years_birth = result['prev_years_birth'],
                    dead_children = result['dead_children'],
                    alive_children = result['alive_children'];
                $scope.dead_children_cards_info = result['dead_children_cards_info'];
                $scope.alive_children_cards_info = result['alive_children_cards_info'];
                $scope.infants_death_coeff = result["infants_death_coeff"].toFixed(2);
                $scope.infants_death = [{
                    "values": dead_children,
                    "key": "Количество умерших детей",
                    "color": "#FF6633",
                    "my_key": 'dead'
                    },
                    {
                    "values": alive_children,
                    "key": "Количество живых детей",
                    "color": "#339933",
                    "my_key": 'alive'
                    }];
                for (var key in prev_years_perinatal_death) {
                    if (prev_years_perinatal_death[key].length) {
                        var color = key == 'РФ' ? "#FF9728" : "#FF6633";
                        $scope.infants_prev_years.push({
                            "key": key + ', смертность',
                            "values": prev_years_perinatal_death[key],
                            "color": color
                        })
                    }
                }
                for (var key in prev_years_birth) {
                    if (prev_years_birth[key].length) {
                        var color = key == 'РФ' ? "#3c8dbc" : "#339933";
                        $scope.infants_prev_years.push({
                            "key": key + ', рождаемость',
                            "values": prev_years_birth[key],
                            "color": color
                        })
                    }
                
                }
            }
        });
    };
    $scope.refresh_gistograms_by_period();
}]);

var IndexOverseer3Ctrl = function ($controller, $scope, RisarApi) {
    $scope.curation_level = {
        code: '3'
    };
    $scope.query = {
        client: undefined,
        search_str: undefined
    };
    $scope.search_date = {date: new Date()}; // и это костыль. этот для работы wmDate
    $scope.tickets = [];

    $controller('BaseDeathDateStatCtrl', {$scope: $scope});

    $scope.onQuickSearchChanged = function () {
        // used in ui-select with ext-select-quick-event-search
        return function (query_str) {
            $scope.query.search_str = query_str;
        }
    };

    $scope.$watch('search_date.date', function (n, o) {
        RisarApi.schedule.get_appointments(n).then(function (tickets) {
            $scope.tickets = tickets;
        })
    });
};

WebMis20.controller('IndexOverseer3Ctrl', ['$controller', '$scope', 'RisarApi',
    IndexOverseer3Ctrl]);
