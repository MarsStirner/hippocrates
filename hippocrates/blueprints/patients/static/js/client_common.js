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

//<--! START VMP Coupon  -->
WebMis20.service('VmpApi', ['$http', 'WMConfig', function ($http, WMConfig) {
    return {
        save: function(client, coupon, coupon_file) {
            return $http.post(WMConfig.url.patients.coupon_save, {
                        client_id: client.client_id,
                        coupon: coupon,
                        coupon_file: coupon_file
                    })
        },
        del: function(coupon) {
            return $http.post(WMConfig.url.patients.coupon_delete, {
                    coupon: coupon
                    })
        },
        parse_xlsx: function(coupon_file) {
            return $http.post(WMConfig.url.patients.coupon_parse, {
                        coupon: coupon_file
                    })
        }
    }
}]);

WebMis20.service('VmpModalService', ['$modal', function ($modal) {
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
            return openVmpCouponModal(client, coupon)
        }
    }
}]);

WebMis20.controller('VmpCtrl', ['$http', '$rootScope', '$scope', 'MessageBox', 'WMConfig', 'WMClientServices', 'VmpModalService', 'VmpApi',
    function ($http, $rootScope, $scope, MessageBox, WMConfig, WMClientServices, VmpModalService, VmpApi) {
        $scope.deleteCoupon = function (client, coupon) {
            VmpApi.del(coupon).success(function () {
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
            VmpModalService.open(client, coupon).then(function(result) {
                VmpApi.save(client, result[0], result[1]).success(function(data) {
                    var coupon = data.result;
                    $rootScope.$broadcast('new_vmp_saved', coupon);
                }).error(function (data) {
                    return MessageBox.error('Ошибка', 'Произошла ошибка добавления талона')
                });
            });
        };
        $scope.$on('new_vmp_saved', function(coupon) {
           if (angular.isDefined(coupon)) {
                if (angular.isDefined(client.vmp_coupons)){ client.vmp_coupons.push(coupon); }

           };
        });
        $scope.removeVmpCoupon = function(client, coupon) {
            MessageBox.question(
                'Удаление талона ВМП',
                'Вы действительно хотите удалить талон ВМП?'
            ).then(function () {
                $scope.deleteCoupon(client, coupon);
            });
        };
}]);

WebMis20.controller('VmpModalCtrl', ['$scope', 'VmpApi', 'WMConfig', 'client', 'coupon',
    function($scope, VmpApi, WMConfig, client, coupon) {
    $scope.coupon_file = {};
    $scope.coupon = coupon;
    $scope.reloadCoupon = function(data) {
        $scope.coupon = data.result;
        $scope.wrong_client = client.client_id != $scope.coupon.client.id;
    };
    $scope.parse_xlsx = function() {
        VmpApi.parse_xlsx($scope.coupon_file).success($scope.reloadCoupon);
    };
}]);
//<--! END VMP Coupon   -->
