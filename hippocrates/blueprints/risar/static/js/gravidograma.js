
'use strict';

var GravidogramaCtrl = function ($scope, RisarApi, RefBookService, PrintingService) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.rbRisarComplaints = RefBookService.get('rbRisarComplaints');
    $scope.blood_pressure = {right_systolic:[],
        right_diastolic: [],
        left_systolic: [],
        left_diastolic: []
    };
    $scope.patient_gravidograma = [];
    $scope.weight_gain = [];
    $scope.weight_gain_upper = [];
    $scope.weight_gain_lower = [];
    $scope.weight_gain_title = '';

    $scope.abdominal = new Array(19);
    $scope.presenting_part = new Array(19);
    $scope.fetus_heart_rate = new Array(19);
    $scope.edema = new Array(19);
    $scope.weight = new Array(19);

    // граничные значения для графика прибавки массы в зависимости от МРК
    var weight_gain_upper_1 = [[36, 0.68], [50, 1.1], [64, 1.3], [78, 1.4], [92, 2.2], [106, 3], [120, 3.7], [134, 4.6], [148, 5.6], [162, 6.5], [176, 7.2],
            [190, 8.01], [204, 8.5], [218, 9.4], [232, 10.1], [246, 10.8], [260, 11.21]];
    var weight_gain_lower_1 = [[36, -0.48], [50, -0.3], [64, 0.3], [78, 0.5], [92, 1.2], [106, 1.8], [120, 2.5], [134, 3.4], [148, 4.2], [162, 5], [176, 5.9],
            [190, 6.61], [204, 7.5], [218, 8.3], [232, 8.9], [246, 9.4], [260, 10.25]];
    var weight_gain_upper_2 = [[36, -0.2], [50, 0.1], [64, 0.3], [78, 0.7], [92, 1.2], [106, 1.5], [120, 2.65], [134, 3.8], [148, 4.2], [162, 4.9], [176, 5.9],
            [190, 6.3], [204, 7], [218, 7.5], [232, 8.5], [246, 8.7], [260, 8.9]];
    var weight_gain_lower_2 = [[36, -1.2], [50, -1.3], [64, -1.25], [78, -0.7], [92, -0.5], [106, 0.5], [120, 1.25], [134, 2.5], [148, 2.9], [162, 3.9], [176, 4.2],
            [190, 4.02], [204, 5.6], [218, 6.5], [232, 7.4], [246, 7.5], [260, 7.7]];
    var weight_gain_upper_3 = [[36, 0.6], [50, 1.1], [64, 1.5], [78, 1.9], [92, 3.5], [106, 4.5], [120, 5.54], [134, 6.5], [148, 7.54], [162, 8.54], [176, 9.1],
            [190, 9.9], [204, 10.9], [218, 11.2], [232, 11.9], [246, 12.5], [260, 12.97]];
    var weight_gain_lower_3 = [[36, -0.6], [50, -0.6], [64, -0.6], [78, 0.5], [92, 1.3], [106, 2.5], [120, 3.74], [134, 4.5], [148, 5.5], [162, 6.5], [176, 7.9],
            [190, 8.9], [204, 9.5], [218, 9.9], [232, 10.8], [246, 11], [260, 11.17]];

    $scope.ps = new PrintingService("risar_gravidograma");
    $scope.ps.set_context("risar_gravidograma");
    $scope.ps_resolve = function () {
        $scope.xml_blood_pressure_right = d3.select('#blood_pressure_right svg').node().parentNode.innerHTML;
        $scope.xml_blood_pressure_left = d3.select('#blood_pressure_right svg').node().parentNode.innerHTML;
        $scope.xml_gravidograma = d3.select('#gravidograma svg').node().parentNode.innerHTML;
        $scope.xml_weight_gain_data = d3.select('#weight_gain_data svg').node().parentNode.innerHTML;

        return {
            event_id: $scope.chart.id,
            blood_pressure_right: $scope.xml_blood_pressure_right,
            blood_pressure_left: $scope.xml_blood_pressure_left,
            gravidograma: $scope.xml_gravidograma,
            weight_gain_data: {chart: $scope.xml_weight_gain_data,
                               title: $scope.weight_gain_title,
                               weight: $scope.weight},
            abdominal: $scope.abdominal,
            fetus_heart_rate: $scope.fetus_heart_rate,
            presenting_part: $scope.presenting_part,
            edema: $scope.edema
        }
    };

    var reload_checkup = function () {
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;

            var first_checkup = $scope.chart.checkups[$scope.chart.checkups.length-1];
            var hw_ratio = first_checkup.height ? Math.round((first_checkup.weight/first_checkup.height)*100) : NaN;

            // прибавка массы
            if (!hw_ratio || (hw_ratio>=35 && hw_ratio<=41)){
                $scope.weight_gain_upper.push.apply($scope.weight_gain_upper, weight_gain_upper_1);
                $scope.weight_gain_lower.push.apply($scope.weight_gain_lower, weight_gain_lower_1);
                $scope.weight_gain_title = 'нормостенического телосложения (M +/- 16; 10,73 +/- 3,25)';
            } else if (hw_ratio >=42) {
                $scope.weight_gain_upper.push.apply($scope.weight_gain_upper, weight_gain_upper_2);
                $scope.weight_gain_lower.push.apply($scope.weight_gain_lower, weight_gain_lower_2);
                $scope.weight_gain_title = 'с ожирением (M +/- 16; 8,3 +/- 2,12)';
            } else {
                $scope.weight_gain_upper.push.apply($scope.weight_gain_upper, weight_gain_upper_3);
                $scope.weight_gain_lower.push.apply($scope.weight_gain_lower, weight_gain_lower_3);
                $scope.weight_gain_title = 'с дефицитом массы теля (M +/- 16; 12,07 +/- 2,8)';
            }
            $scope.refreshCharts();
            var pregnancy_start_date =  moment($scope.chart.card_attributes.pregnancy_start_date);
            for (var i in event.checkups) {
                var checkup = event.checkups[i];
                var checkups_beg_date = moment(checkup.beg_date);
                var day_num = (checkups_beg_date.diff(pregnancy_start_date, 'days')) - 27; // интересует начиная с 5ой недели
                var index = Math.floor(day_num/14);

                $scope.abdominal[index] = checkup.abdominal;
                $scope.fetus_heart_rate[index] = checkup.fetus_heart_rate;

                // предлежание плода
                if (checkup.presenting_part){
                    var short_name = checkup.presenting_part.name.split(' ').reduce(function(prev, curr){
                        var str = prev + curr[0].toUpperCase();
                        return str
                    }, "");
                    $scope.presenting_part[index] = [short_name, checkup.presenting_part.name];
                }

                // проверяем были жалобы на отеки
                if(checkup.complaints){
                    var edema = $scope.rbRisarComplaints.get_by_code("oteki");
                    $scope.edema[index] = indexOf(checkup.complaints, edema)>0 ? '+' : '-';
                }

                // высота стояния дна матки
                if (checkup.fundal_height && day_num>0){
                    $scope.patient_gravidograma.push([day_num, checkup.fundal_height]);
                }

                // давление
                if(checkup.ad_right_high) {$scope.blood_pressure.right_systolic.push([day_num, checkup.ad_right_high])};
                if(checkup.ad_right_low){$scope.blood_pressure.right_diastolic.push([day_num, checkup.ad_right_low])};
                if(checkup.ad_left_high){ $scope.blood_pressure.left_systolic.push([day_num, checkup.ad_left_high])};
                if(checkup.ad_left_low){$scope.blood_pressure.left_diastolic.push([day_num, checkup.ad_left_low])};

                //прибавка массы
                if(checkup.weight && first_checkup.weight){
                    $scope.weight_gain.push([day_num, checkup.weight-first_checkup.weight]);
                    $scope.weight[index] = checkup.weight;
                };
            }
            $scope.refreshCharts();
        })
    };

    $scope.xStr = ['5-6', '7-8', '9-10', '11-12', '13-14', '15-16', '17-18', '19-20', '21-22', '23-24', '25-26',
        '27-28', '29-30', '31-32', '33-34', '35-36', '37-38', '39-40', '41-42'];

    $scope.gravidograma_data = [
        {
        "key": "верхняя граница",
        "values":[[64, 11.5], [78, 15.7], [92, 19], [106, 21.8], [120, 24], [134, 25], [148, 27], [162, 28.7], [176, 31.4],
            [190, 32], [204, 33.9], [218, 35.6], [232, 37.3], [246, 38.2], [260, 35.8]],
        "color": '#FF6633'
        },
        {
        "key": "нижняя граница",
        "values":[[64, 10.8], [78, 12.5], [92, 14], [106, 16.8], [120, 18.8], [134, 21.8], [148, 23.4], [162, 23.7], [176, 26.8],
            [190, 29.4], [204, 31.3], [218, 32.2], [232, 32.7], [246, 35.2], [260, 34.8]],
        "color": '#6699CC'
        },
        {
        "key": "данные пациентки",
        "values": $scope.patient_gravidograma,
        "color": '#66CC33'
        }
    ];

    $scope.blood_pressure_right = [
        {
        "key": "верхняя граница",
        "values":[[0, 130], [266, 130]],
        "color": '#FF6633'
        },
        {
        "key": "нижняя граница",
        "values":[[0, 90], [266, 90]],
        "color": '#6699CC'
        },
        {
        "key": "систолическое",
        "values": $scope.blood_pressure.right_systolic,
        "color": '#339933'
        },
        {
        "key": "диастолическое",
        "values": $scope.blood_pressure.right_diastolic,
        "color": '#66CC33'
        }
    ];

    $scope.blood_pressure_left = [
        {
        "key": "верхняя граница",
        "values":[[0, 130], [266, 130]],
        "color": '#FF6633'
        },
        {
        "key": "нижняя граница",
        "values":[[0, 90], [266, 90]],
        "color": '#6699CC'
        },
        {
        "key": "систолическое",
        "values": $scope.blood_pressure.left_systolic,
        "color": '#339933'
        },
        {
        "key": "диастолическое",
        "values": $scope.blood_pressure.left_diastolic,
        "color": '#66CC33'
        }
    ];

    $scope.weight_gain_data = [
        {
        "key": "верхняя граница",
        "values": $scope.weight_gain_upper,
        "color": '#FF6633'
        },
        {
        "key": "нижняя граница",
        "values": $scope.weight_gain_lower,
        "color": '#6699CC'
        },
        {
        "key": "прибавка массы",
        "values": $scope.weight_gain,
        "color": '#339933'
        }
    ];

    $scope.xAxisTickFormat = function(d){
        return $scope.xStr[Math.floor(d/14)];
    }

    $scope.refreshCharts = function () {
        for (var i = 0; i < nv.graphs.length; i++) {
            nv.graphs[i].update();
            $('svg .nv-lineChart circle.nv-point').css({"fill-opacity": 1});
        }
    };
    reload_checkup();
};