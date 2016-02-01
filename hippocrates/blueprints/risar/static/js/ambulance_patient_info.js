var AmbulancPatientInfoCtrl = function ($scope, RisarApi) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.riskColor = '';
    var reload_patient_info = function () {
        RisarApi.chart.get(event_id)
        .then(function (event) {
            $scope.chart = event;
            if ($scope.chart.risk_rate.code == "low") {
                $scope.riskColor = '#5cb85c';
            } else if ($scope.chart.risk_rate.code == "medium"){
                $scope.riskColor = '#f0ad4e';
            } else if ($scope.chart.risk_rate.code == "high"){
                $scope.riskColor = '#d9534f';
            }
        })
    };
    reload_patient_info();
};
