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
            };
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

WebMis20.controller('VmpModalCtrl', ['$scope', 'ApiCalls', 'WMConfig', 'client', 'coupon',
    function($scope, ApiCalls, WMConfig, client, coupon) {
    $scope.coupon_file = {};
    $scope.coupon = coupon;
    function reloadCoupon (coupon) {
        $scope.coupon = coupon;
        $scope.wrong_client = client.client_id != $scope.coupon.client.id;
        $scope.nonunique = client.vmp_coupons.filter(function (coupon){
            return coupon.number == $scope.coupon.number
        }).length > 0;
        $scope.nonunique = false;
    };
    $scope.parse_xlsx = function() {
        ApiCalls.wrapper('POST', WMConfig.url.patients.coupon_parse, {}, {
            coupon: $scope.coupon_file
        }).then(reloadCoupon);
    };
}]);

WebMis20.service('VmpModalService', ['$modal', '$q', '$http', '$templateCache',
    'WMConfig', 'WMClient', 'MessageBox',
    function ($modal, $q, $http, $templateCache, WMConfig, WMClient, MessageBox) {
    var deferred = $q.defer();
    function openVmpCouponModal (client, coupon) {
        var instance = $modal.open({
        size: 'lg',
        templateUrl: '/nemesis/client/services/modal/edit_vmp_coupon.html',
        backdrop : 'static',
        resolve: {
            client: function () {
                return client;
            },
            coupon: function () {
                return coupon;
            }
        },
        controller: 'VmpModalCtrl'});
        return instance.result
    }
    return {
        open: function(client, coupon) {
            // todo: somehow get rid off^ arguments
            openVmpCouponModal(client, coupon).then(function (result) {
                $http.post(
                    WMConfig.url.patients.coupon_save, {
                        client_id: client.client_id,
                        coupon: result[0],
                        coupon_file: result[1]
                    }
                ).success(function(data) {
                    deferred.resolve(data.result);
                }).error(function (data) {
                    return MessageBox.error(
                        'Ошибка',
                        'Произошла ошибка добавления талона'
                    );
                });
            return deferred.promise;
            })
        }
    }
}]);
WebMis20.controller('VmpCtrl', ['$http', '$scope', 'MessageBox', 'WMConfig', 'WMClientServices', 'VmpModalService',
    function ($http, $scope, MessageBox, WMConfig, WMClientServices, VmpModalService) {
        $scope.deleteCoupon = function (client, coupon) {
            $http.post(
                WMConfig.url.patients.coupon_delete, {
                    coupon: coupon
                }
            ).success(function () {
                WMClientServices.delete_record(client, 'vmp_coupons', coupon)
            });
        };
        $scope.addVmpCoupon = function (client) {
            var coupon = {
                id: null,
                number: 0,
                mkb: null,
                code: '',
                date: null,
                event: null,
                name: '',
                deleted: 0
            };
            VmpModalService.open(client, coupon).then(function (coupon) {
                client.vmp_coupons.push(coupon);
            }, function (coupon) {
                client.vmp_coupons.push(coupon);
            });
        };
        $scope.removeVmpCoupon = function(client, coupon) {
            MessageBox.question(
                'Удаление талона ВМП',
                'Вы действительно хотите удалить талон ВМП?'
            ).then(function () {
                $scope.deleteCoupon(client, coupon);
            });
        };
}]);

