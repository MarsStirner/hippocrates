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
    $scope.saved = [];
    $scope.clipboard = null;
    $scope.MKB = RefBookService.get('MKB');
    $scope.copy_clipboard = function (row) {
        $scope.clipboard = row.diagnoses;
    };
    $scope.paste_clipboard = function (row) {
        row.diagnoses = _.sortBy(_.distinct(row.diagnoses.concat($scope.clipboard.clone()), 'id'), 'code');
    };
    $scope.reset_row = function (index) {
        $scope.list[index].diagnoses = $scope.saved[index].diagnoses.clone();
    };
    $scope.row_equal = function (index) {
        return angular.equals($scope.list[index], $scope.saved[index]);
    };
    $scope.save = function () {
        $http.post('/risar_config/api/routing.json', $scope.list).success(init_data)
    };
    $http.get('/risar_config/api/routing.json').success(init_data);

    var sortDiags = $scope.sortDiags = function (org) {
        org.diagnoses = _.sortBy(org.diagnoses, 'code');
        return org;
    };

    function init_data (data) {
        $scope.list = data.result.map(sortDiags);
        $scope.saved = _.deepCopy($scope.list);
    }
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