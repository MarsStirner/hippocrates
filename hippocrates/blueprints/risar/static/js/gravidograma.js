
'use strict';

var GravidogramaCtrl = function ($scope, RisarApi, RefBookService) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.rbRisarComplaints = RefBookService.get('rbRisarComplaints');

    $scope.data = [];
    $scope.abdominal = new Array(19);
    $scope.presenting_part = new Array(19);
    $scope.fetus_heart_rate = new Array(19);
    $scope.edema = new Array(19);

    var reload_checkup = function () {
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;
            var pregnancy_start_date =  moment($scope.chart.card_attributes.pregnancy_start_date);
            for (var i in event.checkups) {
                var checkups_beg_date = moment(event.checkups[i].beg_date)
                var day_num = (checkups_beg_date.diff(pregnancy_start_date, 'days')) - 27; // интересует начиная с 5ой недели
                var index = Math.floor(day_num/14);

                $scope.abdominal[index] = event.checkups[i].abdominal;
                $scope.fetus_heart_rate[index] = event.checkups[i].fetus_heart_rate;

                if (event.checkups[i].presenting_part){
                    var short_name = event.checkups[i].presenting_part.name.split(' ').reduce(function(prev, curr){
                        var str = prev + curr[0].toUpperCase();
                        return str
                    }, "");
                    $scope.presenting_part[index] = [short_name, event.checkups[i].presenting_part.name];
                }

                if(event.checkups[i].complaints){
                    var edema = $scope.rbRisarComplaints.get_by_code("oteki");
                    $scope.edema[index] = indexOf(event.checkups[i].complaints, edema)>0 ? '+' : '-';
                }


                if (event.checkups[i].fundal_height && day_num>0){
                    $scope.data.push([day_num, event.checkups[i].fundal_height]);
                }
            }
        })
    };

    $scope.xStr = ['5 - 6', '7 - 8', '9 - 10', '11 - 12', '13 - 14', '15 - 16', '17 - 18', '19 - 20', '21 - 22', '23 - 24', '25 - 26',
        '27 - 28', '29 - 30', '31 - 32', '33 - 34', '35 - 36', '37 - 38', '39 - 40', '41 - 42'];

    $scope.gravidograma_data = [
        {
        "key": "верхняя граница",
        "values":[[64, 11.5], [78, 15.7], [92, 19], [106, 21.8], [120, 24], [134, 25], [148, 27], [162, 28.7], [176, 31.4],
            [190, 32], [204, 33.9], [218, 35.6], [232, 37.3], [246, 38.2], [260, 35.8]]
        },
        {
        "key": "нижняя граница",
        "values":[[64, 10.8], [78, 12.5], [92, 14], [106, 16.8], [120, 18.8], [134, 21.8], [148, 23.4], [162, 23.7], [176, 26.8],
            [190, 29.4], [204, 31.3], [218, 32.2], [232, 32.7], [246, 35.2], [260, 34.8]]
        },
        {
        "key": "данные пациентки",
        "values": $scope.data
        }
    ];
    $scope.xAxisTickFormat = function(d){
        return $scope.xStr[Math.floor(d/14)];
    }
    $scope.xFunction = function(){
        return function(d){
            return $scope.xStr[Math.floor(d[0]/14)];
        };
    }

    reload_checkup();
};