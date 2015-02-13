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
        row.diagnoses = _.listSetList(row.diagnoses.concat($scope.clipboard.clone()), 'id');
    };
    $scope.save = function () {
        $http.post('/risar_config/api/routing.json', $scope.list).success(function (data) {
            $scope.list = data.result;
        })
    };
    $http.get('/risar_config/api/routing.json').success(function (data) {
        $scope.list = data.result;
    })
});