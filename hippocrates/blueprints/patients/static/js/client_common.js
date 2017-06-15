'use strict';

WebMis20.service('PatientModalService', ['$modal', '$templateCache', 'WMConfig',
        'WMClient', function ($modal, $templateCache, WMConfig, WMClient) {
    var _openClientModal = function (wmclient) {
        var instance = $modal.open({
            templateUrl: '/WebMis20/modal/client/client_edit.html',
            controller: ClientModalCtrl,
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
    };
    return {
        openClient: function (wmclient, reload) {
            if (reload) {
                return wmclient.reload().then(function () {
                    return _openClientModal(wmclient);
                });
            } else {
                return _openClientModal(wmclient);
            }
        },
        openNewClient: function () {
            var wmclient = new WMClient('new');
            return this.openClient(wmclient, true);
        },
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
