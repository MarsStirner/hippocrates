'use strict';

WebMis20.service('PatientModalService', ['$modal', '$templateCache', 'WMConfig',
        function ($modal, $templateCache, WMConfig) {
    return {
        openSearchItem: function (wmclient) {
            var tUrl = WMConfig.url.patients.patient_search_modal + '?client_id=' +
                wmclient.info.id;
            //$templateCache.remove();
            var instance = $modal.open({
                templateUrl: tUrl,
                controller: ClientSearchModalCtrl,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-scrollable',
                resolve: {
                    client: function () {
                        return wmclient;
                    }
                }
            });
            return instance.result;
        }
    }
}]);


var ClientSearch = function ($scope, $location, WMClient, PatientModalService) {
    $scope.aux = aux;
    $scope.params = aux.getQueryParams(document.location.search);
    $scope.query = $scope.params.q || '';
    $scope.client_id = parseInt($scope.params.client_id) || null;
    $scope.client = null;
    $scope.clientSearchApi = undefined;

    $scope.setSelectedPatient = function (selected_client) {
        var patient_id = selected_client.info.id;
        $scope.client_id = patient_id;
        $scope.updateUrlArgs({client_id: patient_id});
        $scope.client = new WMClient(patient_id);
        $scope.client.reload('for_servicing')
            .then(function () {
                return PatientModalService.openSearchItem($scope.client)
                    .finally(function () {
                        $scope.client = null;
                    });
            });
    };
    $scope.getClientSearchApi = function (api) {
        $scope.clientSearchApi = api;
    };
    $scope.$on('ClientSearchChanged', function (e, args) {
        $scope.updateUrlArgs({q: args.query});
    });
    $scope.updateUrlArgs = function (args) {
        args = angular.extend({}, $location.search(), args);
        $location.search(args).replace();
    };

    // set initial query text
    if ($scope.query) {
        var unwatch = $scope.$watch('clientSearchApi', function (n, o) {
            $scope.clientSearchApi.performSearch($scope.query)
                .then(function (client_info) {
                    if ($scope.client_id &&
                        client_info.some(function (cinfo) {
                            return cinfo.info.id === $scope.client_id;
                        })
                    ) {
                        $scope.setSelectedPatient({info: {id: $scope.client_id}});
                    }
                });
            unwatch();
        });
    }
};

WebMis20.controller('ClientSearch', ['$scope', '$location', 'WMClient', 'PatientModalService', ClientSearch]);
