/**
 * Created by mmalkov on 04.02.15.
 */

angular.module('WebMis20')
.controller('SetupMainCtrl', function ($scope, $window) {
    $scope.page = 0;
})
.controller('RisarRoutingSetup', function ($scope, $http, RefBookService) {
    $scope.query = '';
    $scope.list = [];
    $scope.clipboard = null;
    $scope.MKB = RefBookService.get('MKB');
    $scope.copy_clipboard = function (row) {
        $scope.clipboard = row.diagnoses;
    };
    $scope.paste_clipboard = function (row) {
        row.diagnoses = _.distinct(row.diagnoses.concat($scope.clipboard.clone()), 'id');
    };
    $scope.save = function () {
        $http.post('/risar_config/api/routing.json', $scope.list).success(function (data) {
            $scope.list = data.result;
        })
    };
    $http.get('/risar_config/api/routing.json').success(function (data) {
        $scope.list = data.result;
    })
})
.filter('orgdiag', function () {
    return function (orgs, query) {
        query = query.toUpperCase();
        return orgs.filter(function (org) {
            return !query || org.diagnoses.filter(function (diagnosis) {
                return !query || diagnosis.code.contains(query) || diagnosis.name.toUpperCase().contains(query)
            }).length > 0;
        })
    }
})
;