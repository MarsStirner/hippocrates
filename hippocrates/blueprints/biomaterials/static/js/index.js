WebMis20.controller('BiomaterialsIndexCtrl', [
    '$scope', '$modal', 'ApiCalls', 'WMConfig', 'SelectAll', 'RefBookService', 'PrintingService', 'MessageBox',
    function ($scope, $modal, ApiCalls, WMConfig, SelectAll, RefBookService, PrintingService, MessageBox) {
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
            status: null
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
            ApiCalls.wrapper(
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

        $scope.$watchCollection('filter', function (new_value, old_value) {
            if ($scope.filter.lab && $scope.filter.status != 2) {
                $scope.filter.lab = null;
            }
            $scope.set_current_records();
        });

        $scope.get_data();
    }])
;
