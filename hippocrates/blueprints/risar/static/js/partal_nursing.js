
WebMis20.controller('PartalNursingEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$timeout',
    'RisarApi', 'Config', 'CurrentUser', 'jinjaVariables',
function ($scope, $controller, $window, $location, $document, $timeout, RisarApi, Config, CurrentUser, jinjaVariables) {
    var params = aux.getQueryParams(window.location.search);
    var pp_nursing_id = $scope.pp_nursing_id = params.pp_nursing_id;
    var jv = jinjaVariables;
    $scope.flatcode = jv.flatcode;
    var event_id = $scope.event_id = params.event_id;
    $scope.pp_nursing = pp_nursing_id ===undefined ? {person: CurrentUser, date: new Date()} : {};
    $scope.save = function () {
            return RisarApi.partal_nursing.save($scope.flatcode, event_id, $scope.pp_nursing).then(function (data) {

                if ($scope.pp_nursing.hasOwnProperty('id')) {
                    $scope.pp_nursing = data;
                } else {
                    //в урле нужно отобразить pp_nursing_id
                    $window.open(Config.url.partal_nursing_edit_html.format($scope.flatcode)+'?event_id='+event_id+'&pp_nursing_id='+data.id, '_self');
                };
            });
    };
    var reload = function () {
        RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
        });
        if (pp_nursing_id !== undefined) {
            RisarApi.partal_nursing.get($scope.flatcode, pp_nursing_id, event_id).then(function (data) {
                    $scope.pp_nursing = data;
            }, function (error) {
                // редиректим на создание нового патронажа
                $window.open(Config.url.partal_nursing_edit_html.format($scope.flatcode)+'?event_id='+event_id, '_self');
            });
        }
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



