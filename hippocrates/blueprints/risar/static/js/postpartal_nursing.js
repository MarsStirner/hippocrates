/**
 * Created by mmalkov on 24.07.16.
 */
WebMis20.controller('PartalNursingEditCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$timeout',
    'RisarApi', 'Config', 'CurrentUser',
function ($scope, $controller, $window, $location, $document, $timeout, RisarApi, Config, CurrentUser) {
    var params = aux.getQueryParams(window.location.search);
    var pp_nursing_id = $scope.pp_nursing_id = params.pp_nursing_id;
    var event_id = $scope.event_id = params.event_id;
    $scope.pp_nursing = pp_nursing_id ===undefined ? {person: CurrentUser, date: new Date()} : {};
    $scope.save = function () {
            return RisarApi.postpartal_nursing.save(event_id, $scope.pp_nursing).then(function (data) {
                if ($scope.pp_nursing.hasOwnProperty('id')) {
                    $scope.pp_nursing = data;
                } else {
                    //в урле нужно отобразить pp_nursing_id
                    $window.open(Config.url.postpartal_nursing_edit.format(event_id)+'&pp_nursing_id='+data.id, '_self');
                };
            });
    };
    var reload = function () {
        RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
                $scope.minDate = $scope.header.event.set_date;
        });
        if (pp_nursing_id !== undefined) {
            RisarApi.postpartal_nursing.get(pp_nursing_id, event_id).then(function (data) {
                    $scope.pp_nursing = data;
            }, function (error) {
                //редиректим на создание нового патронажа
                $window.open(Config.url.postpartal_nursing_edit.format(event_id), '_self');
            });
        }
    };
    reload();
}])
.controller('PartalNursingListCtrl', ['$scope', '$controller', '$window', '$location', '$document', '$filter', 'RisarApi', 'Config',
function ($scope, $controller, $window, $location, $document, $filter, RisarApi, Config) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    function reload () {
        RisarApi.chart.get_header(event_id).then(function (data) {
                $scope.header = data.header;
        });
        RisarApi.postpartal_nursing.get_list(event_id).then(function (data) {
                $scope.nursing_list = $filter('orderBy')(data.postpartal_nursing_list, 'date');
        });
    };
    reload();
}]);



