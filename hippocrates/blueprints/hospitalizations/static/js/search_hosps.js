'use strict';

var CurrentHospsCtrl = function ($scope, $filter, HospitalizationsService, EventModalService,
        SelectAll, PrintingService, CurrentUser, TimeoutCallback) {
    var curDate = moment();
    $scope.date_range = {
        current_day: true,
        date: aux.format_date(curDate),
        start: curDate.set({hour: 8, minute: 0, second: 0}).toDate(),
        end: curDate.clone().add('d', 1).toDate()
    };
    $scope.filter = {
        org_struct: CurrentUser.info.org_structure,
        hosp_status: null
    };
    $scope.staticFilter = {
        client_full_name: '',
        set_person_name: '',
        external_id: ''
    };
    $scope.pager = {
        current_page: 1,
        per_page: 75,
        max_pages: 10,
        pages: null,
        record_count: null
    };
    $scope._orig_hosp_list = [];
    $scope.hosp_list = [];
    $scope.hosps_stats = {};
    $scope.hospsByDoctorText = '';
    $scope.ps_elist = new PrintingService('event_list');
    $scope.selectedRecords = new SelectAll([]);

    $scope.toggleHistoryView = function () {
        $scope.date_range.current_day = !$scope.date_range.current_day;
        if ($scope.date_range.current_day) {
            $scope.date_range.start = curDate.clone().set({hour: 8, minute: 0, second: 0}).toDate();
            $scope.date_range.end = curDate.clone().add('d', 1).toDate();
        }
    };
    $scope.isCurDayView = function () {
        return $scope.date_range.current_day;
    };
    $scope.isHistoryView = function () {
        return !$scope.date_range.current_day;
    };
    $scope.quickFilterActive = function () {
        return $scope.staticFilter.client_full_name ||
            $scope.staticFilter.set_person_name ||
            $scope.staticFilter.external_id;
    };
    var quickFilterRecords = function (records) {
        if (!$scope.quickFilterActive()) {
            return records;
        }
        var flt_cfn = $scope.staticFilter.client_full_name.toLowerCase(),
            flt_spn = $scope.staticFilter.set_person_name.toLowerCase(),
            flt_eid = $scope.staticFilter.external_id.toLowerCase();

        return _.filter(records, function(value){
            return (
                !flt_cfn || value.client.full_name.toLowerCase().indexOf(flt_cfn) !== -1
            ) && (
                !flt_spn || value.exec_person.short_name.toLowerCase().indexOf(flt_spn) !== -1
            ) && (
                !flt_eid || value.external_id.toLowerCase().indexOf(flt_eid) !== -1
            );
        });
    };

    var setHospListData = function (hosp_list) {
        var qfilterActive = $scope.quickFilterActive();
        $scope._orig_hosp_list = hosp_list;
        if (qfilterActive) {
            $scope.hosp_list = quickFilterRecords(hosp_list);
        } else {
            $scope.hosp_list = hosp_list;
        }

        if (!qfilterActive) {
            $scope.selectedRecords.setSource(_.pluck($scope.hosp_list, 'id'));
            $scope.selectedRecords.selectNone();
        }
    };
    var refreshHospList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var args = {
            paginate: true,
            page: $scope.pager.current_page,
            per_page: $scope.pager.per_page,
            for_date: $scope.isCurDayView() ? $scope.date_range.date : undefined,
            start_dt: $scope.isHistoryView() ? $scope.date_range.start : undefined,
            end_dt: $scope.isHistoryView() ? $scope.date_range.end : undefined,
            org_struct_id: safe_traverse($scope.filter, ['org_struct', 'id']) || undefined,
            hosp_status: safe_traverse($scope.filter, ['hosp_status', 'id']) || undefined,
            history: $scope.isHistoryView()
        };
        return HospitalizationsService.get_hosp_list(args)
            .then(function (paged_data) {
                $scope.pager.record_count = paged_data.count;
                $scope.pager.pages = paged_data.total_pages;
                setHospListData(paged_data.items);
            });
    };
    var refreshHospsStats = function () {
        var args = {
            for_date: $scope.isCurDayView() ? $scope.date_range.date : undefined,
            start_dt: $scope.isHistoryView() ? $scope.date_range.start : undefined,
            end_dt: $scope.isHistoryView() ? $scope.date_range.end : undefined,
            org_struct_id: safe_traverse($scope.filter, ['org_struct', 'id']) || undefined,
            hosp_status: safe_traverse($scope.filter, ['hosp_status', 'id']) || undefined,
            history: $scope.isHistoryView()
        };
        return HospitalizationsService.get_hosps_stats(args)
            .then(function (data) {
                $scope.hosps_stats = data;
                makeCountByDoctorsDescription();
            });
    };
    var makeCountByDoctorsDescription = function () {
        $scope.hospsByDoctorText = _.chain(_.values($scope.hosps_stats.count_current_by_doctor))
            .sortBy(function (info) {
                return info.person_name;
            })
            .map(function (info) {
                return '<span class="nowrap">{0} - <b>{1}</b></span>'.format(
                    info.person_name, info.events_count);
            })
            .value()
            .join(', ');
    };

    $scope.getData = function (quick_filter) {
        refreshHospsStats();
        return refreshHospList();
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
    $scope.movingClosed = function (hosp) {
        return Boolean(safe_traverse(hosp, ['moving', 'end_date']));
    };
    var updateHospRecordMoving = function (hosp, moving) {
        hosp.moving.id = moving.id;
        hosp.moving.end_date = moving.end_date;
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
    $scope.makeMovingTransfer = function (hosp, is_final) {
        EventModalService.openMakeTransfer(hosp.id, hosp.moving.id, is_final)
            .then(function (movings) {
                var upd_cur_moving = movings[0];
                if (is_final) {
                    updateHospRecordMoving(hosp, upd_cur_moving);
                } else {
                    refreshHospList(true);
                    refreshHospsStats();
                }
            });
    };
    $scope.viewEventInfo = function (hosp) {
        EventModalService.openHospitalisationInfo(hosp.id);
    };
    $scope.getVisibleSelectedRecords = function () {
        return _.intersection(
            $scope.selectedRecords.selected(),
            _.pluck($scope.hosp_list, 'id')
        );
    };
    $scope.visibleRecordsAllSelected = function () {
        return $scope.hosp_list.length && $scope.selectedRecords.selected().length &&
            $scope.getVisibleSelectedRecords().length === $scope._orig_hosp_list.length;
    };
    $scope.toggleAllVisibleRecords = function () {
        var enabled = !$scope.visibleRecordsAllSelected();
        _.each($scope.hosp_list, function (hosp) {
            $scope.selectedRecords.select(hosp.id, enabled);
        });
    };
    $scope.ps_elist_resolve = function () {
        return {
            event_id_list: $scope.getVisibleSelectedRecords()
        };
    };
    $scope.canChangeOrgStruct = function () {
        return CurrentUser.current_role_in('admin');
    };
    $scope.controlsAvailable = function () {
        return !$scope.isHistoryView();
    };
    $scope.getHbDaysText = function (hosp) {
        return '{0}{ (с |1|)}'.formatNonEmpty(
            hosp.hb_days,
            hosp.hb_days !== null ?
                $filter('asDateTime')(hosp.move_date) :
                null
        );
    };

    var tc = new TimeoutCallback($scope.getData, 600);
    var watch_with_reload = function (n, o) {
        if (angular.equals(n, o)) return;
        tc.start();
    };
    var watch_without_reload = function (n, o) {
        if (angular.equals(n, o)) return;
        setHospListData($scope._orig_hosp_list);
    };

    $scope.$watch('date_range.start', watch_with_reload);
    $scope.$watch('date_range.end', watch_with_reload);
    $scope.$watch('filter.org_struct', watch_with_reload);
    $scope.$watch('filter.hosp_status', watch_with_reload);
    $scope.$watch('staticFilter', watch_without_reload, true);

    tc.start();
};

WebMis20.controller('CurrentHospsCtrl', ['$scope', '$filter', 'HospitalizationsService',
    'EventModalService', 'SelectAll', 'PrintingService', 'CurrentUser', 'TimeoutCallback',
    CurrentHospsCtrl]);
