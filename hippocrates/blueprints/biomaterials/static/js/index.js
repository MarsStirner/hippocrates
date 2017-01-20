WebMis20.controller('BiomaterialsIndexCtrl', [
    '$scope', '$modal', '$window', '$interval', '$q', 'ApiCalls', 'WMConfig', 'SelectAll', 'RefBookService',
    'PrintingService', 'PrintingDialog', 'MessageBox', 'CurrentUser',
    function ($scope, $modal, $window, $interval, $q,ApiCalls, WMConfig, SelectAll, RefBookService,
              PrintingService, PrintingDialog, MessageBox, CurrentUser) {
        $scope.selected_records = new SelectAll([]);
        $scope.TTJStatus = RefBookService.get('TTJStatus');
        $scope.rbLaboratory = RefBookService.get('rbLaboratory');
        $scope.ps_bm = new PrintingService("biomaterials");
        $scope.ps_bm.set_context("biomaterials");

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
        $scope.requestInProgress = false;
        $scope.refreshCanceller = undefined;

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

        $scope.quickFilterActive = function () {
            return $scope.static_filter.client__full_name ||
                $scope.static_filter.set_persons__name ||
                $scope.static_filter.action_type__name;
        };
        var quickFilterRecords = function (records) {
            if (!$scope.quickFilterActive()) {
                return records;
            }
            var flt_cfn = $scope.static_filter.client__full_name.toLowerCase(),
                flt_spn = $scope.static_filter.set_persons__name.toLowerCase(),
                flt_atn = $scope.static_filter.action_type__name.toLowerCase();

            return _.filter(records, function(value){
                return (
                    !flt_cfn || value.client.full_name.toLowerCase().indexOf(flt_cfn) !== -1
                ) && (
                    !flt_spn || value.set_persons.some(function (sp) {
                        return sp.short_name.toLowerCase().indexOf(flt_spn) !== -1
                    })
                ) && (
                    !flt_atn || value.actions.some(function (act) {
                        return act.action_type.name.toLowerCase().indexOf(flt_atn) !== -1
                    })
                );
            });
        };
        var filterTubes = function (records) {
            var tubes = {};
            _.each(records, function (rec) {
                var tube_key = rec.testTubeType.code;
                if (_.has(tubes, tube_key)) {
                    tubes[tube_key].count += rec.actions.length;
                } else {
                    tubes[tube_key] = {
                        count: rec.actions.length,
                        name: rec.testTubeType.name
                    };
                }
            });
            return tubes;
        };

        $scope.set_current_records = function (quick_filter, dont_refresh_selected) {
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
                    var records = [], tubes = [];
                    if (quick_filter) {
                        records = quickFilterRecords(value.records);
                        tubes = filterTubes(records);
                    } else {
                        records = value.records;
                        tubes = value.tubes;
                    }

                    result.records = result.records.concat(records);
                    _.each(tubes, function (tube_value, tube_key) {
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
            $scope.grouped_current_result = _.groupBy($scope.current_result.records, function(row) {
                return row.client.full_name;
            });

            if (!quick_filter && !dont_refresh_selected) {
                $scope.selected_records.setSource(_.pluck($scope.current_result.records, 'id'));
                $scope.selected_records.selectNone();
            }

            // resize block
            setTimeout(function(){
                var victim = document.getElementsByClassName('autoheight')[0];
                while (window.innerHeight < document.body.scrollHeight && victim.offsetHeight > 60) {
                  victim.style['max-height'] = victim.offsetHeight - 3 + 'px';
                }
            }, 200);
        };

        $scope.get_data = function (quick_filter, dont_refresh_selected) {
            $scope.requestInProgress = true;
            $scope.refreshCanceller = $q.defer();
            return ApiCalls.wrapper(
                'POST', WMConfig.url.biomaterials.api_get_ttj_records,
                {}, {filter: $scope.filter}, { timeout: $scope.refreshCanceller.promise }
            )
                .then(function (res) {
                    $scope.result = res;
                    $scope.set_current_records(quick_filter, dont_refresh_selected);
                })
                .finally(function () {
                    $scope.requestInProgress = false;
                });
        };

        $scope.change_status = function (status) {
            var chosen_records = $scope.getVisibleSelectedRecords();

            ApiCalls.wrapper('POST', WMConfig.url.biomaterials.api_ttj_update_status, {},
                {
                    ids: chosen_records,
                    status: $scope.TTJStatus.get_by_code(status)
                }
            )
                .then(function () {
                    return $scope.get_data($scope.quickFilterActive(), true);
                })
                .then(function () {
                    // reset checkboxes on sended
                    _.each(chosen_records, function(sel) {
                        $scope.selected_records.select(sel, false);
                    });

                    PrintingDialog.open($scope.ps_bm, $scope.ps_resolve(chosen_records), {}, true, 'biomaterials');
                });
        };

        $scope.getVisibleSelectedRecords = function () {
            return _.intersection($scope.selected_records.selected(), _.pluck($scope.current_result.records, 'id'));
        };
        $scope.ps_resolve = function (manual_values) {
            if (!$scope.getVisibleSelectedRecords().length && manual_values === undefined) {
                return MessageBox.error('Печать невозможна', 'Выберите хотя бы один забор биоматериала');
            }
            return {
                ttj_ids: manual_values ? manual_values : $scope.getVisibleSelectedRecords()
            }
        };
        $scope.visibleAllSelected = function () {
            return $scope.current_result.records &&
                $scope.getVisibleSelectedRecords().length === $scope.current_result.records.length;
        };
        $scope.toggleAllVisibleRecords = function () {
            var enabled = !$scope.visibleAllSelected();
            _.each($scope.current_result.records, function (record) {
                $scope.selected_records.select(record.id, enabled);
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
        $scope.isPaidAction = function (action) {
            return action.payment && action.payment.pay_status.code === 'paid';
        };
        $scope.isNotPaidAction = function (action) {
            return action.payment && action.payment.pay_status.code === 'not_paid';
        };
        $scope.isRefundedAction = function (action) {
            return action.payment && action.payment.pay_status.code === 'refunded';
        };

        function watch_with_reload(n, o) {
            if (angular.equals(n, o)) return;
            if ($scope.filter.lab && $scope.filter.status != 2) {
                $scope.filter.lab = null;
            }
            $scope.get_data();
        }

        function watch_without_reload(n, o) {
            if (angular.equals(n, o)) return;
            if ($scope.filter.lab && $scope.filter.status != 2) {
                $scope.filter.lab = null;
            }
            $scope.set_current_records(true);
        }

        $scope.barCodeSearch = function(model) {
            if ($scope.refreshCanceller) {
                $scope.refreshCanceller.resolve('cancel search');
            }
            $scope.get_data();
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

        var reload = $interval(function () {
            if (!$scope.requestInProgress) {
                $scope.get_data($scope.quickFilterActive(), true);
            }
        }, 60000);
        $scope.get_data();
    }])
;
