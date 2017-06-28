
WebMis20.service('ClientAttachModalService', ['$modal', function ($modal) {
    function openСlientAttachModal (client, client_attach, client_attaches) {
        var instance = $modal.open({
        size: 'lg',

        templateUrl: '/nemesis/client/services/modal/edit_client_attach.html',
        backdrop : 'static',
        resolve: {
            client: function () {
                return client;
            },
            client_attach: function () {
                return client_attach;
            },
            client_attaches: function() {
                return client_attaches;
            }
        },
        controller: 'ClientAttachModalCtrl'});
        return instance.result
    }
    return {
        open: function(client, client_attach, client_attaches) {
            return openСlientAttachModal(client, client_attach, client_attaches)
        }
    }
}]);

WebMis20.controller('ClientAmbCardCtrl', ['$http', '$rootScope', '$scope', 'MessageBox', 'WMConfig', 'WMClientServices', 'ClientAttachModalService', 'WebMisApi',
    function ($http, $rootScope, $scope, MessageBox, WMConfig, WMClientServices, ClientAttachModalService, WebMisApi) {
        $scope.deleteClientAttach = function (client, client_attach, idx) {
            WebMisApi.client_attach.del(client_attach).then(function () {
                 $scope.client_attaches.splice(idx, 1)
            });
        };
        $scope.open = function (client, client_attach) {
            ClientAttachModalService.open(client, client_attach, angular.copy($scope.client_attaches)).then(function (result) {
                WebMisApi.client_attach.save(client, result[0]).then(function (client_attach) {
                    $scope.reloadAmbCard(client.client_id);
                }, function (data) {
                    return MessageBox.error('Ошибка', 'Произошла ошибка прикрепления пациента')
                });
            });
        };
        $scope.addClientAttach = function (client) {
            var client_attach = {
                id: null,
                begDate: null,
                endDate: null,
                person: null,
                deleted: 0,
                amb_card_id: safe_traverse($scope, ['amb_card', 'id'])
            };
            $scope.open(client, client_attach);
        };
        $scope.removeClientAttach = function(client, client_attach, idx) {
            MessageBox.question(
                'Удаление прикрепления клиента',
                'Вы действительно хотите удалить прикрепление клиента?'
            ).then(function () {
                $scope.deleteClientAttach(client, client_attach, idx);
            });
        };
        $scope.editClientAttach = function (client, client_attach) {
            $scope.open(client, angular.copy(client_attach));
        };
        $scope.reloadAmbCard = function(client_id) {
            WebMisApi.client_attach.get(client_id).then(function (response) {
                $scope.amb_card = response['amb_card'];
                $scope.client_attaches = response['client_attaches'];
            });
        };
        $scope.$watch('client_attaches', function(n, o) {
            $scope.isAddAvailable  = true;
            if (n) {
                var itemsNumber = n ? n.length : 0,
                    haslastEndDate = itemsNumber ? !moment(n[itemsNumber-1].endDate).isValid(): false;
                if (itemsNumber > 0 && haslastEndDate) {
                    $scope.isAddAvailable = false;
                }
            }
        });
}]);

WebMis20.controller('ClientAttachModalCtrl', ['$scope', 'WebMisApi', 'WMConfig', 'client', 'client_attach', 'client_attaches',
    function($scope, WebMisApi, WMConfig, client, client_attach, client_attaches) {
    $scope.client_attach = client_attach;
    $scope.client_attaches = client_attaches;
    $scope.largestBegDate = null;
    $scope.hasIntersectionWithAnotherRecords = function (client_attach) {
        $scope.intersectsWith = [];
        var current_range = moment.range(moment(client_attach.begDate), moment(client_attach.endDate));
        _.map($scope.client_attaches, function (item, key) {
            var itemBegDate = moment(item.begDate),
                range = moment.range(moment(item.begDate), moment(item.endDate));
            $scope.largestBegDate = itemBegDate.clone();
            if (item.id!=client_attach.id) {
                var begDate = moment(client_attach.begDate);
                if (current_range.overlaps(range) || current_range.adjacent(range) || range.contains(begDate)
                ) { $scope.intersectsWith.push(item); }
            }
        });
        if ($scope.largestBegDate && $scope.largestBegDate.isValid()) {
            $scope.largestBegDate.add(1, 'd');
        }
        return $scope.intersectsWith.length > 0;
    }
    $scope.hasIntersectionWithAnotherRecords(client_attach);

    $scope.$watchCollection("[client_attach.begDate, client_attach.endDate]", function (n, o) {
        var st = moment(n[0]),
            end =moment(n[1]);

        if (st.isAfter(end)) {
             end = st.clone().add(1, 'd');
             $scope.client_attach.endDate = end.clone().toDate();
         }
    });

    $scope.$watch('client_attach', function(n, o) {
        $scope.isSaveUnAvailable  = true;
        if (n) {
            var begDate = moment(n.begDate);
            if (safe_traverse(n, ['person', 'id'])
                && begDate.isValid()
                && !$scope.hasIntersectionWithAnotherRecords(n)
                ) {
                $scope.isSaveUnAvailable  = false;
            }
        }
    }, true);
}])


 WebMis20.run(['$templateCache', function ($templateCache) {
        $templateCache.put(
            '/nemesis/client/services/modal/edit_client_attach.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title" id="myModalLabel">Прикрепление клиента</h4>\
            </div>\
            <div class="modal-body">\
                <div class="row" ng-repeat="(key, value) in intersectsWith">\
                    <div class="col-md-offset-1">\
                        <span style="color:red">Пересекается с уже существующим прикреплением <b>[[value.begDate|asDate]]</b> - <b>[[value.endDate|asDate]]</b></span>\
                    </div>\
                </div>\
                <div class="row">\
                            <div class="col-md-4" ng-class="{\'has-error\': !client_attach.person}"\>\
                                <label for="person">Врач</label>\
                                <wm-person-select id="filter-set-person" ng-model="client_attach.person"></wm-person-select>\
                            </div>\
                            <div class="col-md-3">\
                                <label for="beg_date">Дата начала</label>\
                                <wm-date id="beg_date" min-date="largestBegDate"  ng-model="client_attach.begDate" ng-required="true"></wm-date>\
                            </div>\
                            <div class="col-md-3">\
                                <label for="end_date">Дата окончания</label>\
                                <wm-date id="end_date" min-date="client_attach.begDate" ng-model="client_attach.endDate" ></wm-date>\
                            </div>\
                </div>\
            <div class="modal-footer">\
                <div class="pull-right">\
                    <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
                    <button class="btn btn-success" ng-disabled="isSaveUnAvailable"\
                    ng-click="$close([client_attach])">Сохранить</button>\
                </div>\
            </div>\
')}]);
