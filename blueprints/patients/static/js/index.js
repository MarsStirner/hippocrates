/**
 * Created by mmalkov on 11.07.14.
 */
var ClientSearch = function ($scope, $http, $timeout, $window, PrintingService) {
    $scope.ps = new PrintingService('registry');
    $scope.ps_resolve = function (client_id) {
        return {
            client_id: client_id
        }
    };
    $scope.ps.set_context('token');
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.query = "";
    $scope.results = [];
    $scope.alerts = [];
    var _timeoutObjectForQuery;

    $scope.$watch('query', function (val) {
        if (_timeoutObjectForQuery) $timeout.cancel(_timeoutObjectForQuery);
        _timeoutObjectForQuery = $timeout(function () {
            $scope.results = null;
            $scope.perform_search(val);
        }, 500)
    });

    $scope.perform_search = function (val) {
        if (!val) {
            $scope.results = [];
        } else {
            $http.get(
                url_client_search, {
                    params: {
                        q: val
                    }
                }
            ).success(function (data) {
                    $scope.results = data.result;
                })
        }
    };

    $scope.open_client = function (client_id) {
        window.open(url_client_html + '?client_id=' + client_id, '_self');
    };

    $scope.$on('printing_error', function (event, error) {
        $scope.alerts.push(error);
    });

    $scope.query_clear = function () {
        $scope.query = '';
    }
};
WebMis20.controller('ClientSearch', ['$scope', '$http', '$timeout', '$window', 'PrintingService', ClientSearch]);
