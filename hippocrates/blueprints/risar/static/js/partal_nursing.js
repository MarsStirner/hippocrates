
WebMis20.controller('PartalNursingEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$timeout',
    'RisarApi', 'Config', 'CurrentUser', 'jinjaVariables',
function ($scope, $controller, $window, $location, $document, $timeout, RisarApi, Config, CurrentUser, jinjaVariables) {
    var params = aux.getQueryParams(window.location.search),
        pp_nursing_id = $scope.pp_nursing_id = params.pp_nursing_id,
        jv = jinjaVariables,
        event_id = $scope.event_id = params.event_id,
        initialCheckup = {person: CurrentUser, date: new Date()};

    $controller('commonPrintCtrl', {$scope: $scope});
    $scope.flatcode = jv.flatcode;
    $scope.pp_nursing = {};
    if (pp_nursing_id === undefined) {
        angular.copy(initialCheckup, $scope.pp_nursing);
    }
    $scope.mother_anamnesis = {};
    $scope.father_anamnesis = {};
    $scope.save = function () {
            return RisarApi.partal_nursing.save(pp_nursing_id, $scope.flatcode, event_id,
                {pp_nursing: $scope.pp_nursing,
                mother_anamnesis: $scope.mother_anamnesis,
                father_anamnesis: $scope.father_anamnesis,
                }
            ).then(function (data) {
                if ($scope.pp_nursing.hasOwnProperty('id')) {
                    $scope.pp_nursing = data['pp_nursing'];
                    $scope.mother_anamnesis = data['mother_anamnesis'];
                    $scope.father_anamnesis = data['father_anamnesis'];
                } else {
                    //в урле нужно отобразить pp_nursing_id
                    $window.open(Config.url.partal_nursing_edit_html.format($scope.flatcode)+'?event_id='+event_id+'&pp_nursing_id='+data['pp_nursing'].id, '_self');
                };
            });
    };
    var reload = function () {
        RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
        });
        // pp_nursing_id = pp_nursing_id || '';
        var pp_send_id = pp_nursing_id || '';
        RisarApi.partal_nursing.get($scope.flatcode, pp_send_id, event_id).then(function (data) {

            if (pp_nursing_id === undefined) {
                    angular.extend(data['pp_nursing'], $scope.pp_nursing);
            } else {
                    $scope.pp_nursing = data['pp_nursing'];
            }
            $scope.mother_anamnesis = data['mother_anamnesis'];
            $scope.father_anamnesis = data['father_anamnesis'];
        }, function (error) {
            // // редиректим на создание нового патронажа
            // $window.open(Config.url.partal_nursing_edit_html.format($scope.flatcode)+'?event_id='+event_id, '_self');
        });

    };
    reload();
}])
.controller('PartalNursingListCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$filter', 'RisarApi', 'Config', 'jinjaVariables',
function ($scope, $controller, $window, $location, $document, $filter, RisarApi, Config, jinjaVariables) {
    var jv = jinjaVariables;
    $scope.flatcode = jv.flatcode === 'postpartal_nursing' ? 'postpartal_nursing' : 'prepartal_all';
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.path_to_read = Config.url.partal_nursing_read_html;
    $scope.path_to_edit = Config.url.partal_nursing_edit_html;
    $controller('commonPrintCtrl', {$scope: $scope});
    function reload () {
        RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
        });
        RisarApi.partal_nursing.get_list($scope.flatcode, event_id).then(function (data) {
            $scope.nursing_list = $filter('orderBy')(data[$scope.flatcode+'_list'], 'date');
        });
    };
    reload();
}]);



