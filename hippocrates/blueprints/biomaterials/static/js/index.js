WebMis20.controller('BiomaterialsIndexCtrl', [
    '$scope', '$modal', '$window', 'ApiCalls', 'WMConfig', 'SelectAll', 'RefBookService', 'PrintingService', 'PrintingDialog', 'MessageBox', 'CurrentUser', '$interval',
    function ($scope, $modal, $window, ApiCalls, WMConfig, SelectAll, RefBookService, PrintingService, PrintingDialog, MessageBox, CurrentUser, $interval) {
        $scope.selected_records = new SelectAll([]);
        $scope.TTJStatus = RefBookService.get('TTJStatus');
        $scope.rbLaboratory = RefBookService.get('rbLaboratory');
        $scope.ps_bm = new PrintingService("biomaterials");
        $scope.ps_bm.set_context("biomaterials");

        $scope.ps_resolve = function (manual_values) {
            if (!$scope.selected_records.any() && manual_values === undefined) {
                return MessageBox.error('Печать невозможна', 'Выберите хотя бы один забор биоматериала');
            }
            return {
                ttj_ids: manual_values ? manual_values : $scope.selected_records.selected()
            }
        };

        $scope.filter = {
            barCode: null,
            execDate: new Date(),
            status: 0,
            org_struct: CurrentUser.info.org_structure
        };

        $scope.static_filter = {
            client__full_name: '',
            set_persons__name: '',
            action_type__name: ''
        };

        $scope.current_result = [];
        $scope.grouped_current_result = {};

        $scope.count_all_records = function () {
            return _.chain($scope.result).mapObject(
                function (value) { return value.records.length }
            ).values().reduce(
                function (a, b) { return a + b }
            ).value();
        };

        $scope.count_finished_records = function () {
            return _.chain($scope.result).mapObject(
                function (value, key) { return ['finished', 'sent_to_lab', 'fail_to_lab'].has(key)?value.records.length:0 }
            ).values().reduce(
                function (a, b) { return a + b }
            ).value();
        };

        var reload = $interval(function(){
            $scope.get_data();
        }, 60000);

        $scope.set_current_records = function () {
            var display_map = {
                null: ['waiting', 'finished', 'sent_to_lab', 'fail_to_lab'],
                waiting: ['waiting'],
                // in_progress: ['in_progress'],
                finished: ['finished', 'sent_to_lab', 'fail_to_lab']
            };
            var result = {
                records: [],
                tubes: {}
            };
            var status = $scope.filter.status !== null ? $scope.TTJStatus.get($scope.filter.status).code : 'null';
            var cats = display_map[status];
            _.chain($scope.result)
                .filter(function (value, key) {
                    return cats.has(key)
                })
                .each(function (value) {
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

            // static filter
            if($scope.static_filter.client__full_name
                || $scope.static_filter.set_persons__name
                || $scope.static_filter.action_type__name) {

                result.records = _.chain(result.records)
                    .filter(function(value){
                        return value.client.full_name.toLowerCase().indexOf($scope.static_filter.client__full_name.toLowerCase()) !== -1;
                    })
                    .filter(function(value){
                        var sps =_.filter(value.set_persons, function(sp) {
                            return sp.short_name.toLowerCase().indexOf($scope.static_filter.set_persons__name.toLowerCase()) !== -1;
                        });
                        return Object.keys(sps).length;
                    })
                    .filter(function(value){
                        var acts =_.filter(value.actions, function(act) {
                            return act.action_type.name.toLowerCase().indexOf($scope.static_filter.action_type__name.toLowerCase()) !== -1;
                        });
                        return Object.keys(acts).length;
                    })
                    .value();
            }

            $scope.current_result = result;

            // group result by client name
            $scope.grouped_current_result = _.groupBy($scope.current_result.records, function(row){
                return row.client.full_name;
            });

            // var prev_selected = _.intersection($scope.selected_records.selected(), _.pluck($scope.current_result.records, 'id'));
            $scope.selected_records.setSource(_.pluck($scope.current_result.records, 'id'));
            // $scope.selected_records.selectNone();
            // _.each(prev_selected, function(sel){
            //     $scope.selected_records.select(sel, true);
            // });

            // resize block
            setTimeout(function(){
                var victim = document.getElementsByClassName('autoheight')[0];
                while (window.innerHeight < document.body.scrollHeight && victim.offsetHeight > 0) {
                  victim.style['max-height'] = victim.offsetHeight - 1 + 'px';
                }
            }, 200);
        };

        $scope.get_data = function () {
            return ApiCalls.wrapper(
                'POST',
                WMConfig.url.biomaterials.api_get_ttj_records, {}, {filter: $scope.filter}
            )
                .then(_.passThrough(function (res) {
                    $scope.result = res;
                    $scope.set_current_records();
                }), _.passThrough($scope.set_current_records));
        };

        $scope.change_status = function (status) {
            var remember_selected = _.intersection($scope.selected_records.selected(), _.pluck($scope.current_result.records, 'id'));

            ApiCalls.wrapper(
                'POST',
                WMConfig.url.biomaterials.api_ttj_update_status, {},
                {
                    ids: remember_selected,
                    status: $scope.TTJStatus.get_by_code(status)
                })
                .then($scope.get_data, $scope.get_data)
                .then(function () {
                    // reset checkboxes on sended
                    _.each(remember_selected, function(sel){
                        $scope.selected_records.select(sel, false);
                    });

                    PrintingDialog.open($scope.ps_bm, $scope.ps_resolve(remember_selected), {}, true, 'biomaterials');
                });
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

        $scope.barCodeSearch = function(model){
            watch_with_reload(model);
        };

        // $scope.$watch('filter.barCode', watch_with_reload);
        $scope.$watch('filter.execDate', watch_with_reload);
        $scope.$watch('filter.lab', watch_with_reload);
        $scope.$watch('filter.org_struct', watch_with_reload);
        $scope.$watch('filter.biomaterial', watch_with_reload);

        $scope.$watch('filter.status', watch_without_reload);
        $scope.$watch('static_filter.client__full_name', watch_without_reload);
        $scope.$watch('static_filter.set_persons__name', watch_without_reload);
        $scope.$watch('static_filter.action_type__name', watch_without_reload);

        $scope.get_data();
    }])
;
