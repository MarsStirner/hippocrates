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
            return openVmpCouponModal(client, coupon)
        }
    }
}]);

WebMis20.controller('VmpCtrl', ['$http', '$rootScope', '$scope', 'MessageBox', 'WMConfig', 'WMClientServices', 'VmpModalService', 'WebMisApi',
    function ($http, $rootScope, $scope, MessageBox, WMConfig, WMClientServices, VmpModalService, WebMisApi) {
        $scope.deleteCoupon = function (client, coupon) {
            WebMisApi.vmp.del(coupon).then(function () {
                WMClientServices.delete_record(client, 'vmp_coupons', coupon)
            });
        };
        $scope.addVmpCoupon = function (client) {
            $scope.client = client;
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
                WebMisApi.vmp.save(client, result[0], result[1]).then(function(coupon) {
                    $rootScope.$broadcast('new_vmp_saved', {coupon: coupon});
                }, function (data) {
                    return MessageBox.error('Ошибка', 'Произошла ошибка добавления талона')
                });
            });
        };
        $scope.$on('new_vmp_saved', function(event, data) {
           if (angular.isDefined($scope.client) && angular.isDefined(data.coupon)) {
                if (angular.isDefined($scope.client.vmp_coupons)){ $scope.client.vmp_coupons.push(data.coupon); }
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

WebMis20.controller('VmpModalCtrl', ['$scope', 'WebMisApi', 'WMConfig', 'client', 'coupon',
    function($scope, WebMisApi, WMConfig, client, coupon) {
    $scope.coupon_file = {};
    $scope.coupon = coupon;
    $scope.reloadCoupon = function(coupon) {
        $scope.coupon = coupon;
        $scope.wrong_client = client.client_id != $scope.coupon.client.id;
    };
    $scope.parse_xlsx = function() {
        WebMisApi.vmp.parse_xlsx($scope.coupon_file).then($scope.reloadCoupon);
    };
}])

 WebMis20.run(['$templateCache', function ($templateCache) {
        $templateCache.put(
            '/nemesis/client/services/modal/edit_vmp_coupon.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title" id="myModalLabel">Загрузка талона ВМП</h4>\
            </div>\
            <div class="modal-body">\
                <div class="row marginal">\
                    <div class="col-md-8">\
                        <input type="file" wm-input-file file="coupon_file"\
                               accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
                    </div>\
                    <div class="col-md-4">\
                        <button type="button" ng-disabled="!coupon_file.name" class="btn btn-default btn-sm" ng-click="parse_xlsx()">Загрузить</button>\
                    </div>\
                </div>\
                <div class="row" ng-if="coupon.number">\
                    <div class="col-md-12">\
                        <b>После загрузки файла проверьте правильность данных:</b>\
                    </div>\
                </div>\
                <div class="row" ng-if="wrong_client">\
                    <div class="col-md-12 text-danger">\
                        <b>Внимание! Убедитесь, что талон пренадлежит текущему пациенту!</b>\
                    </div>\
                </div>\
                <div class="row">\
                    <div class="col-md-12" ng-if="coupon.number">\
                        <table class="table table-condensed">\
                            <tbody>\
                                <tr>\
                                    <th>Пациент</th>\
                                    <th>[[coupon.client.name]]</th>\
                                </tr>\
                                <tr>\
                                    <th>№ талона</th>\
                                    <td>[[coupon.number]]</td>\
                                </tr>\
                                <tr>\
                                    <th>Диагноз</th>\
                                    <td>[[coupon.mkb.code]] [[coupon.mkb.name]]</td>\
                                </tr>\
                                <tr>\
                                    <th>Код ВМП</th>\
                                    <td>[[coupon.quota_type.code]]</td>\
                                </tr>\
                                <tr>\
                                    <th>дата планируемой госпитализации</th>\
                                    <td>[[coupon.date | asDate]]</td>\
                                </tr>\
                            </tbody>\
                        </table>\
                    </div>\
                </div>\
                <div class="row" ng-if="coupon.number">\
                    <div class="col-md-12">\
                        <b>Если данные верные - сохраните талон</b>\
                    </div>\
                </div>\
            </div>\
            <div class="modal-footer">\
                <div class="pull-right">\
                    <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
                    <button ng-disabled="!coupon.is_unique" class="btn btn-success" ng-click="$close([coupon, coupon_file])">Сохранить</button>\
                </div>\
            </div>\
')}]);
