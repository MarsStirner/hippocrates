
'use strict';

var MaternalCertModalCtrl =  function ($scope, $modal, RisarApi, event_id) {
    $scope.maternal_cert = {};
    $scope.saveAndClose = function() {
        RisarApi.maternal_cert.save($scope.maternal_cert).then(function(cert) {
            $scope.$close(cert);
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
};
WebMis20
.service('MaternalCertModalService', ['$modal', 'RisarApi', function ($modal, RisarApi) {
    return {
        openMaternal: function (event_id) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/maternal_cert.html',
                backdrop: 'static',
                controller: MaternalCertModalCtrl,
                size: 'lg',
                resolve: {
                    event_id: function () {
                        return event_id
                    }
                }
            });
            return instance.result
        }
    }
}])
.controller('MaternalCertModalCtrl', ['$scope', '$modal', 'RisarApi', MaternalCertModalCtrl]);
