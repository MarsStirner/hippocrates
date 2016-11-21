'use strict';

WebMis20.controller('SocProfCtrl', ['$scope', '$modal', '$timeout','$controller',  'RisarApi', 'CurrentUser', 'PrintingService', 'PrintingDialog',
function ($scope, $modal, $timeout, $controller, RisarApi, CurrentUser, PrintingService, PrintingDialog) {
    $controller('commonPrintCtrl', {$scope: $scope});
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;

    $scope.selectedStage = 'mother_employment';

    var reloadChart = function () {
        var header = RisarApi.chart.get_header(event_id).then(function (data) {
            $scope.header = data.header;
        });
        RisarApi.soc_prof_help.get_list(event_id).then(function (data) {
            $scope.soc_prof_help = data['soc_prof_help'];
        });
    };
    $scope.isStageSelected = function (stage) {
        return stage === $scope.selectedStage;
    };
    $scope.selectStage = function (stage) {
        $scope.selectedStage = stage;
    };
    reloadChart();
    $scope.add = function (flatcode) {
        var model = {};
        open_edit(model, flatcode).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            var data = angular.extend({person:CurrentUser}, result);
            RisarApi.soc_prof_help.save($scope.event_id, flatcode, data).then(function (result) {
                $scope.soc_prof_help[flatcode+'_list'].push(result);
            });
            if (restart) {
                $timeout($scope.add(flatcode))
            }
        })
    };
    $scope.edit = function (p, flatcode) {
        var model = angular.extend({}, p);
        open_edit(model, flatcode).result.then(function (rslt) {
            var result = rslt[0],
                restart = rslt[1];
            RisarApi.soc_prof_help.save($scope.event_id, flatcode, result).then(function (result) {
                angular.extend(p, result);
            });
            if (restart) {
                $timeout($scope.add(flatcode))
            }
        });
    };
    $scope.remove = function (p) {
        if (p.id) {
            RisarApi.soc_prof_help.delete(p.id).then(function () {
                p.deleted = 1;
            });
        } else {
            p.deleted = 1;
        }
    };
    $scope.restore = function (p) {
        if (p.id) {
            RisarApi.soc_prof_help.undelete(p.id).then(function () {
                p.deleted = 0;
            });
        } else {
            p.deleted = 0;
        }
    };
    var open_edit = function (p, flatcode) {
        var scope = $scope.$new();
        scope.model = p;
        scope.minDate = $scope.header.client.birth_date;
        var template_url = '/WebMis20/RISAR/modal/soc_prof_help/{0}.html'.format(flatcode)
        scope.maxDate = new Date();
        return $modal.open({
            templateUrl: template_url,
            scope: scope,
            resolve: {
                model: function () {return p}
            },
            size: 'lg'
        })
    };
}]);