
'use strict';

WebMis20
.service('MaternalCertModalService', ['$modal', 'RisarApi', function ($modal, RisarApi) {
    return {
        openMaternal: function () {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/maternal_cert.html',
                backdrop: 'static',
                controller: 'MaternalCertModalCtrl',
                size: 'lg'
            });
            return instance.result
        },
        saveOnClose: function (maternal_cert) {
            return RisarApi.maternal_cert.save(maternal_cert);
        }

    }
}])
.controller('MaternalCertModalCtrl', ['$scope', '$modal', 'RisarApi',
    function ($scope, $modal, RisarApi) {
        
    var params = aux.getQueryParams(window.location.search);
    var event_id = params.event_id;
    $scope.maternal_cert = {};
    $scope.saveAndClose = function() {
        RisarApi.maternal_cert.save($scope.maternal_cert).then(function() {
            // $scope.$close();
        });
    };
    var reload = function () {
        RisarApi.maternal_cert.get_by_event(event_id).then(function (cert) {
            if ( cert !== null ) {
                $scope.maternal_cert = cert;
            }
        });
        $scope.maternal_cert.event_id = event_id;
    };
    reload();
}]);
