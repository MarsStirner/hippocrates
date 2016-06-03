WebMis20.controller('BiomaterialsIndexCtrl', [
    '$scope', '$modal', '$window', 'ApiCalls', 'WMConfig', 'SelectAll', 'RefBookService', 'PrintingService', 'MessageBox', 'CurrentUser',
    function ($scope, $modal, $window, ApiCalls, WMConfig, SelectAll, RefBookService, PrintingService, MessageBox, CurrentUser) {
        $scope.selected_records = new SelectAll([]);
        $scope.TTJStatus = RefBookService.get('TTJStatus');
        $scope.rbLaboratory = RefBookService.get('rbLaboratory');
        $scope.ps_bm = new PrintingService("biomaterials");
        $scope.ps_bm.set_context("biomaterials");
        $scope.ps_resolve = function () {
            if (!$scope.selected_records.any()) {
                return MessageBox.error('Печать невозможна', 'Выберите хотя бы один забор биоматериала');
            }
            return {
                ttj_ids: $scope.selected_records.selected()
            }
        };
        $scope.filter = {
            execDate: new Date(),
            status: null,
            org_struct: CurrentUser.info.org_structure
        };
        $scope.current_result = [];
        $scope.set_current_records = function () {
            if ($scope.filter.status !== null) {
                $scope.current_result = $scope.result[$scope.TTJStatus.get($scope.filter.status).code]
            } else {
                var result = {
                    records: [],
                    tubes: {}
                };
                _.each($scope.result, function (value) {
                    result.records = result.records.concat(value.records);
                    _.each(value.tubes, function (tube_value, tube_key) {
                        if (_.has(result.tubes, tube_key)) {
                            result.tubes[tube_key].count += tube_value.count
                        } else {
                            result.tubes[tube_key] = {
                                count: tube_value.count,
                                name: tube_value.name
                            };
                        }
                    })
                });
                $scope.current_result = result;
            }
            $scope.selected_records.setSource(_.pluck($scope.current_result.records, 'id'));
            $scope.selected_records.selectNone();
        };
        $scope.get_data = function () {
            return ApiCalls.wrapper(
                'POST',
                WMConfig.url.api_get_ttj_records, {}, {filter: $scope.filter}
            ).then(_.passThrough(function (res) {
                $scope.result = res;
                $scope.set_current_records();
            }), _.passThrough($scope.set_current_records));
        };
        $scope.change_status = function (status) {
            ApiCalls.wrapper(
                'POST',
                WMConfig.url.api_ttj_update_status, {},
                {
                    ids: $scope.selected_records.selected(),
                    status: $scope.TTJStatus.get_by_code(status)
                }).then($scope.get_data, $scope.get_data)
        };

        $scope.open_info = function (record) {
            var scope = $scope.$new();
            scope.model = record;
            return $modal.open({
                templateUrl: 'modal-ttj-info.html',
                backdrop: 'static',
                scope: scope,
                size: 'lg'
            })
        };
        $scope.open_action = function (action_id) {
            $window.open(WMConfig.url.actions.action_html + '?action_id=' + action_id)
        };

        function watch_with_reload(n, o) {
            if (angular.equals(n, o)) return;
            if ($scope.filter.lab && $scope.filter.status != 2) {
                $scope.filter.lab = null;
            }
            $scope.get_data().then(_.passThrough($scope.set_current_records));
        }
        function watch_without_reload(n, o) {
            if (angular.equals(n, o)) return;
            if ($scope.filter.lab && $scope.filter.status != 2) {
                $scope.filter.lab = null;
            }
            $scope.set_current_records();
        }

        $scope.$watch('filter.execDate', watch_with_reload);
        $scope.$watch('filter.lab', watch_with_reload);
        $scope.$watch('filter.org_struct', watch_with_reload);
        $scope.$watch('filter.biomaterial', watch_with_reload);
        $scope.$watch('filter.status', watch_without_reload);

        $scope.get_data();
    }])
;
