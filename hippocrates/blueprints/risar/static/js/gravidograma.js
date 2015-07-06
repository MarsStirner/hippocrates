
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
    var weight_gain_upper_1 = [[35, 0.68], [49, 1.1], [63, 1.3], [77, 1.4], [91, 2.2], [105, 3], [119, 3.7], [133, 4.6], [147, 5.6], [161, 6.5], [174, 7.2],
            [189, 8.01], [203, 8.5], [217, 9.4], [231, 10.1], [245, 10.8], [259, 11.21]];
    var weight_gain_lower_1 = [[35, -0.48], [49, -0.3], [63, 0.3], [77, 0.5], [91, 1.2], [105, 1.8], [119, 2.5], [133, 3.4], [147, 4.2], [161, 5], [174, 5.9],
            [189, 6.61], [203, 7.5], [217, 8.3], [231, 8.9], [245, 9.4], [259, 10.25]];
    var weight_gain_upper_2 = [[35, -0.2], [49, 0.1], [63, 0.3], [77, 0.7], [91, 1.2], [105, 1.5], [119, 2.65], [133, 3.8], [147, 4.2], [161, 4.9], [174, 5.9],
            [189, 6.3], [203, 7], [217, 7.5], [231, 8.5], [245, 8.7], [259, 8.9]];
    var weight_gain_lower_2 = [[35, -1.2], [49, -1.3], [63, -1.25], [77, -0.7], [91, -0.5], [105, 0.5], [119, 1.25], [133, 2.5], [147, 2.9], [161, 3.9], [174, 4.2],
            [189, 4.02], [203, 5.6], [217, 6.5], [231, 7.4], [245, 7.5], [259, 7.7]];
    var weight_gain_upper_3 = [[35, 0.6], [49, 1.1], [63, 1.5], [77, 1.9], [91, 3.5], [105, 4.5], [119, 5.54], [133, 6.5], [147, 7.54], [161, 8.54], [174, 9.1],
            [189, 9.9], [203, 10.9], [217, 11.2], [231, 11.9], [245, 12.5], [259, 12.97]];
    var weight_gain_lower_3 = [[35, -0.6], [49, -0.6], [63, -0.6], [77, 0.5], [91, 1.3], [105, 2.5], [119, 3.74], [133, 4.5], [147, 5.5], [161, 6.5], [174, 7.9],
            [189, 8.9], [203, 9.5], [217, 9.9], [231, 10.8], [245, 11], [259, 11.17]];

    $scope.ps = new PrintingService("risar_gravidograma");
    $scope.ps.set_context("risar_gravidograma");
    $scope.ps_resolve = function () {
        $scope.xml_blood_pressure_right = d3.select('#blood_pressure_right svg').node().parentNode.innerHTML;
        $scope.xml_blood_pressure_left = d3.select('#blood_pressure_right svg').node().parentNode.innerHTML;
        $scope.xml_gravidograma = d3.select('#gravidograma svg').node().parentNode.innerHTML;
        $scope.xml_weight_gain_data = d3.select('#weight_gain_data svg').node().parentNode.innerHTML;

        return {
            event_id: $scope.event_id,
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
        RisarApi.chart.get_header(event_id).
            then(function (data) {
                $scope.header = data.header;
            });
        RisarApi.gravidograma.get(event_id)
        .then(function (result) {
            $scope.checkups = result.checkups;
            $scope.card_attributes = result.card_attributes;

            var first_checkup = $scope.checkups.length ? $scope.checkups[0] : null;
            var hw_ratio = first_checkup && first_checkup.height ? Math.round((first_checkup.weight/first_checkup.height)*100) : NaN;

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
            var pregnancy_start_date =  moment($scope.card_attributes.pregnancy_start_date);
            for (var i in $scope.checkups) {
                var checkup = $scope.checkups[i];
                var checkups_beg_date = moment(checkup.beg_date);
                var day_num = (checkups_beg_date.diff(pregnancy_start_date, 'days')) - 28; // интересует начиная с 5ой недели
                var index = Math.floor(day_num/14);

                if(checkup.abdominal){
                    $scope.abdominal[index] = $scope.abdominal[index] ?
                        $scope.abdominal[index] + ', ' + checkup.abdominal : checkup.abdominal;
                }

                if(checkup.fetus_heart_rate){
                    $scope.fetus_heart_rate[index] = $scope.fetus_heart_rate[index] ?
                        $scope.fetus_heart_rate[index] + ', ' + checkup.fetus_heart_rate : checkup.fetus_heart_rate
                }
                ;

                // предлежание плода
                if (checkup.presenting_part){
                    var short_name = checkup.presenting_part.name.split(' ').reduce(function(prev, curr){
                        var str = prev + curr[0].toUpperCase();
                        return str
                    }, "");
                    if($scope.presenting_part[index]){
                        $scope.presenting_part[index].push([short_name, checkup.presenting_part.name]);
                    } else{
                        $scope.presenting_part[index] = [[short_name, checkup.presenting_part.name]];
                    }
                }

                // проверяем были жалобы на отеки
                if(checkup.complaints){
                    var edema = $scope.rbRisarComplaints.get_by_code("oteki");
                    var if_edema = indexOf(checkup.complaints, edema)>0 ? '+' : '-'
                    $scope.edema[index] = $scope.edema[index] ? $scope.edema[index] + ', '+ if_edema : if_edema;
                }

                // высота стояния дна матки
                if (checkup.fundal_height && day_num>=0){
                    $scope.patient_gravidograma.push([day_num, checkup.fundal_height]);
                }

                // давление
                if(checkup.ad_right_high) {$scope.blood_pressure.right_systolic.push([day_num, checkup.ad_right_high])};
                if(checkup.ad_right_low){$scope.blood_pressure.right_diastolic.push([day_num, checkup.ad_right_low])};
                if(checkup.ad_left_high){ $scope.blood_pressure.left_systolic.push([day_num, checkup.ad_left_high])};
                if(checkup.ad_left_low){$scope.blood_pressure.left_diastolic.push([day_num, checkup.ad_left_low])};

                //прибавка массы
                if(checkup.weight && first_checkup.weight && day_num>=0){
                    $scope.weight_gain.push([day_num, checkup.weight-first_checkup.weight]);
                    $scope.weight[index] = $scope.weight[index] ? $scope.weight[index] + ', ' + checkup.weight : checkup.weight;
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
        "values":[[63, 11.5], [77, 15.7], [91, 19], [105, 21.8], [119, 24], [133, 25], [147, 27], [161, 28.7], [175, 31.4],
            [189, 32], [203, 33.9], [217, 35.6], [231, 37.3], [245, 38.2], [259, 35.8]],
        "color": '#FF6633'
        },
        {
        "key": "нижняя граница",
        "values":[[63, 10.8], [77, 12.5], [91, 14], [105, 16.8], [119, 18.8], [133, 21.8], [147, 23.4], [161, 23.7], [175, 26.8],
            [189, 29.4], [203, 31.3], [217, 32.2], [231, 32.7], [245, 35.2], [259, 34.8]],
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