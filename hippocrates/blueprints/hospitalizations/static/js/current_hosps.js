'use strict';

var CurrentHospsCtrl = function ($scope, $interval, HospitalizationsService,
        EventModalService, SelectAll, PrintingService, MessageBox, CurrentUser) {
    var curDate = moment();
    $scope.date_range = {
        date: aux.format_date(curDate),
        start: curDate.set({hour: 8, minute: 0, second: 0}),
        end: curDate.clone().add('d', 1).set({hour: 7, minute: 59, second: 59})
    };
    $scope.filter = {
        org_struct: CurrentUser.info.org_structure
    };
    $scope.static_filter = {
        client__full_name: ''
    };
    $scope.pager = {
        current_page: 1,
        per_page: 15,
        max_pages: 10,
        pages: null,
        record_count: null
    };
    $scope.hosp_list = [];

    var setHospListData = function (paged_data) {
        $scope.hosp_list = paged_data.items;
        $scope.pager.record_count = paged_data.count;
        $scope.pager.pages = paged_data.total_pages;
    };
    var refreshHospList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var args = {
            paginate: true,
            page: $scope.pager.current_page,
            per_page: $scope.pager.per_page,
            for_date: $scope.date_range.date,
            org_struct_id: safe_traverse($scope.filter, ['org_struct', 'id']) || undefined
        };
        return HospitalizationsService.get_current_hosps(args).then(setHospListData);
    };

    $scope.getData = function (quick_filter, dont_refresh_selected) {
        return refreshHospList()
            .then(function () {
                // $scope.set_current_records(quick_filter, dont_refresh_selected);
            })
    };
    $scope.onPageChanged = function () {
        refreshHospList(true);
    };

    $scope.isHospBedSelected = function (hosp) {
        return safe_traverse(hosp, ['moving', 'id']) && hosp.hosp_bed_name;
    };
    $scope.firstMovingMissing = function (hosp) {
        return !safe_traverse(hosp, ['moving', 'id']);
    };
    var updateHospRecordMoving = function (hosp, moving) {
        hosp.moving.id = moving.id;
        hosp.org_struct_name = moving.orgStructStay.value.name;
        hosp.hosp_bed_name = moving.hospitalBed.value.name;
    };
    $scope.createFirstMoving = function (hosp) {
        EventModalService.openMakeMoving(hosp.id, hosp.received.id, true)
            .then(function (upd_moving) {
                updateHospRecordMoving(hosp, upd_moving);
            });
    };
    $scope.editMoving = function (hosp) {
        EventModalService.openEditMoving(hosp.id, hosp.moving.id)
            .then(function (upd_moving) {
                updateHospRecordMoving(hosp, upd_moving);
            });
    };
//    $scope.count_all_records = function () {
//        return _.chain($scope.result).mapObject(
//            function (value) { return value.records.length }
//        ).values().reduce(
//            function (a, b) { return a + b }
//        ).value();
//    };
//
//    $scope.count_finished_records = function () {
//        return _.chain($scope.result).mapObject(
//            function (value, key) { return ['finished', 'sent_to_lab', 'fail_to_lab'].has(key)?value.records.length:0 }
//        ).values().reduce(
//            function (a, b) { return a + b }
//        ).value();
//    };
//
//    $scope.quickFilterActive = function () {
//        return $scope.static_filter.client__full_name ||
//            $scope.static_filter.set_persons__name ||
//            $scope.static_filter.action_type__name;
//    };
//    var quickFilterRecords = function (records) {
//        if (!$scope.quickFilterActive()) {
//            return records;
//        }
//        var flt_cfn = $scope.static_filter.client__full_name.toLowerCase(),
//            flt_spn = $scope.static_filter.set_persons__name.toLowerCase(),
//            flt_atn = $scope.static_filter.action_type__name.toLowerCase();
//
//        return _.filter(records, function(value){
//            return (
//                !flt_cfn || value.client.full_name.toLowerCase().indexOf(flt_cfn) !== -1
//            ) && (
//                !flt_spn || value.set_persons.some(function (sp) {
//                    return sp.short_name.toLowerCase().indexOf(flt_spn) !== -1
//                })
//            ) && (
//                !flt_atn || value.actions.some(function (act) {
//                    return act.action_type.name.toLowerCase().indexOf(flt_atn) !== -1
//                })
//            );
//        });
//    };
//
//    $scope.set_current_records = function (quick_filter, dont_refresh_selected) {
//        var display_map = {
//            null: ['waiting', 'finished', 'sent_to_lab', 'fail_to_lab'],
//            waiting: ['waiting'],
//            // in_progress: ['in_progress'],
//            finished: ['finished', 'sent_to_lab', 'fail_to_lab']
//        };
//        var result = {
//            records: [],
//            tubes: {}
//        };
//        var status = $scope.filter.status !== null ? $scope.TTJStatus.get($scope.filter.status).code : 'null';
//        var cats = display_map[status];
//        _.chain($scope.result)
//            .filter(function (value, key) {
//                return cats.has(key)
//            })
//            .each(function (value) {
//                var records = [], tubes = [];
//                if (quick_filter) {
//                    records = quickFilterRecords(value.records);
//                    tubes = filterTubes(records);
//                } else {
//                    records = value.records;
//                    tubes = value.tubes;
//                }
//
//                result.records = result.records.concat(records);
//                _.each(tubes, function (tube_value, tube_key) {
//                    if (_.has(result.tubes, tube_key)) {
//                        result.tubes[tube_key].count += tube_value.count
//                    } else {
//                        result.tubes[tube_key] = {
//                            count: tube_value.count,
//                            name: tube_value.name
//                        };
//                    }
//                })
//            });
//
//        $scope.current_result = result;
//        $scope.grouped_current_result = _.groupBy($scope.current_result.records, function(row) {
//            return row.client.full_name;
//        });
//
//        if (!quick_filter && !dont_refresh_selected) {
//            $scope.selected_records.setSource(_.pluck($scope.current_result.records, 'id'));
//            $scope.selected_records.selectNone();
//        }
//
//    };
//
//
//
//    $scope.getVisibleSelectedRecords = function () {
//        return _.intersection($scope.selected_records.selected(), _.pluck($scope.current_result.records, 'id'));
//    };
//    $scope.ps_resolve = function (manual_values) {
//        if (!$scope.getVisibleSelectedRecords().length && manual_values === undefined) {
//            return MessageBox.error('Печать невозможна', 'Выберите хотя бы один забор биоматериала');
//        }
//        return {
//            ttj_ids: manual_values ? manual_values : $scope.getVisibleSelectedRecords()
//        }
//    };
//    $scope.visibleAllSelected = function () {
//        return $scope.current_result.records &&
//            $scope.getVisibleSelectedRecords().length === $scope.current_result.records.length;
//    };
//    $scope.toggleAllVisibleRecords = function () {
//        var enabled = !$scope.visibleAllSelected();
//        _.each($scope.current_result.records, function (record) {
//            $scope.selected_records.select(record.id, enabled);
//        });
//    };
//
//
    function watch_with_reload(n, o) {
        if (angular.equals(n, o)) return;
        $scope.getData();
    }
//
//    function watch_without_reload(n, o) {
//        if (angular.equals(n, o)) return;
//        if ($scope.filter.lab && $scope.filter.status != 2) {
//            $scope.filter.lab = null;
//        }
//        $scope.set_current_records(true);
//    }
//
//    $scope.barCodeSearch = function(barcode) {
//        $scope.get_data();
//    };
//
//    // $scope.$watch('filter.barCode', watch_with_reload);
//    $scope.$watch('filter.execDate', watch_with_reload);
//    $scope.$watch('filter.lab', watch_with_reload);
    $scope.$watch('filter.org_struct', watch_with_reload);
//    $scope.$watch('filter.biomaterial', watch_with_reload);
//
//    $scope.$watch('filter.status', watch_without_reload);
//    $scope.$watch('static_filter.client__full_name', watch_without_reload);
//    $scope.$watch('static_filter.set_persons__name', watch_without_reload);
//    $scope.$watch('static_filter.action_type__name', watch_without_reload);
//
//    var reload = $interval(function () {
//        $scope.get_data($scope.quickFilterActive(), true);
//    }, 60000);

    $scope.getData();
};

WebMis20.controller('CurrentHospsCtrl', ['$scope', '$interval', 'HospitalizationsService',
    'EventModalService', 'RefBookService', 'PrintingService', 'MessageBox',
    'CurrentUser', CurrentHospsCtrl]);
