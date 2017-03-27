WebMis20.controller('BaseDeathDateStatCtrl', ['$scope', 'RisarApi', function ($scope, RisarApi) {
    $scope.refresh_gistograms_by_period = function () {
        return
    };

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

    $scope.closeChosenCards = function () {
        $scope.card_info_at_this_point = [];
    };
    $scope.card_info_at_this_point = [];
    $scope.$on('elementClick.directive', function (angularEvent, event) {
        $scope.$apply(function () {
             $scope.card_info_at_this_point =  $scope.maternal_cards_info[event.pointIndex];
        });
    });

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
    $scope.alive_children_cards = [];
    $scope.dead_children_cards = [];
     $scope.closeChosenCards = function () {
        $scope.alive_children_cards = [];
        $scope.dead_children_cards = [];
    };
    $scope.$on('elementClick.directive', function (angularEvent, event) {
        $scope.$apply(function () {
             $scope.alive_children_cards = $scope.alive_children_cards_info[event.pointIndex];
             $scope.dead_children_cards = $scope.dead_children_cards_info[event.pointIndex];
        });
    });
   
    $scope.refresh_gistograms_by_period = function () {
        //todo: ^should be another separate url
        RisarApi.perinatal_death_stats.get_period($scope.dt.start_date, $scope.dt.end_date).then(function (result) {
            $scope.infants_prev_years = [];
            $scope.infants_death = [];
            $scope.dt_range = result["dt_range"];
            if (result) {
                var prev_years_perinatal_death = result['prev_years_perinatal_death'],
                    prev_years_birth = result['prev_years_birth'],
                    dead_children = result['dead_children'],
                    alive_children = result['alive_children'];
                $scope.dead_children_cards_info = result['dead_children_cards_info'];
                $scope.alive_children_cards_info = result['alive_children_cards_info'];
                $scope.infants_death_coeff = result["infants_death_coeff"].toFixed(2);
                $scope.infants_death = [
                    {
                    "values": alive_children,
                    "key": "Количество живых детей",
                    "color": "#339933",
                    "my_key": 'alive'
                    },
                    {
                    "values": dead_children,
                    "key": "Количество умерших детей",
                    "color": "#FF6633",
                    "my_key": 'dead'
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