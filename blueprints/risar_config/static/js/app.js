/**
 * Created by mmalkov on 04.02.15.
 */

RisarSetupApp = angular.module('RisarSetupApp', ['ngSanitize', 'ui.bootstrap', 'formstamp', 'WebMis20.']);
RisarSetupApp.config(function ($interpolateProvider, $tooltipProvider) {
    $interpolateProvider.startSymbol('[[');
    $interpolateProvider.endSymbol(']]');
    $tooltipProvider.setTriggers({
        'mouseenter': 'mouseleave',
        'click': 'click',
        'focus': 'blur',
        'never': 'mouseleave',
        'show_popover': 'hide_popover'
    })
});

RisarSetupApp.controller('SetupMainCtrl', function ($scope, $window) {
    $scope.page = 0;
    $scope.save = function () {
    }
});

RisarSetupApp.controller('RisarRoutingSetup', function ($scope, $http, RefBookService) {
    $scope.query = '';
    $scope.list = [];
    $scope.clipboard = null;
    $scope.MKB = RefBookService.get('MKB');
    $scope.copy_clipboard = function (row) {
        $scope.clipboard = row.diagnoses;
    };
    $scope.paste_clipboard = function (row) {};
    $scope.save = function () {
        $http.post('/risar_config/api/routing.json', $scope.list);
    };
    $http.get('/risar_config/api/routing.json').success(function (data) {
        $scope.list = data.result;
    })
});