'use strict';

var CurrentHospsCtrl = function ($scope, HospitalizationsService, EventModalService,
        SelectAll, PrintingService, CurrentUser) {
    var curDate = moment();
    $scope.date_range = {
        date: aux.format_date(curDate),
        start: curDate.set({hour: 8, minute: 0, second: 0}),
        end: curDate.clone().add('d', 1).set({hour: 7, minute: 59, second: 59})
    };
    $scope.filter = {
        org_struct: CurrentUser.info.org_structure
    };
    $scope.staticFilter = {
        client_full_name: '',
        set_person_name: ''
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
    $scope.ps_elist = new PrintingService('event_list');
    $scope.selectedRecords = new SelectAll([]);

    $scope.quickFilterActive = function () {
        return $scope.staticFilter.client_full_name ||
            $scope.staticFilter.set_person_name;
    };
    var quickFilterRecords = function (records) {
        if (!$scope.quickFilterActive()) {
            return records;
        }
        var flt_cfn = $scope.staticFilter.client_full_name.toLowerCase(),
            flt_spn = $scope.staticFilter.set_person_name.toLowerCase();

        return _.filter(records, function(value){
            return (
                !flt_cfn || value.client.full_name.toLowerCase().indexOf(flt_cfn) !== -1
            ) && (
                !flt_spn || value.exec_person.short_name.toLowerCase().indexOf(flt_spn) !== -1
            );
        });
    };

    var setHospListData = function (hosp_list, quick_filter) {
        $scope._orig_hosp_list = hosp_list;
        if (quick_filter) {
            $scope.hosp_list = quickFilterRecords(hosp_list);
        } else {
            $scope.hosp_list = hosp_list;
        }

        if (!quick_filter) {
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
            for_date: $scope.date_range.date,
            org_struct_id: safe_traverse($scope.filter, ['org_struct', 'id']) || undefined
        };
        return HospitalizationsService.get_current_hosps(args)
            .then(function (paged_data) {
                $scope.pager.record_count = paged_data.count;
                $scope.pager.pages = paged_data.total_pages;
                setHospListData(paged_data.items);
            });
    };

    $scope.getData = function (quick_filter) {
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

    var watch_with_reload = function (n, o) {
        if (angular.equals(n, o)) return;
        $scope.getData();
    };
    var watch_without_reload = function (n, o) {
        if (angular.equals(n, o)) return;
        setHospListData($scope._orig_hosp_list, true);
    };

    $scope.$watch('filter.org_struct', watch_with_reload);
    $scope.$watch('staticFilter', watch_without_reload, true);

    $scope.getData();
};

WebMis20.controller('CurrentHospsCtrl', ['$scope', 'HospitalizationsService',
    'EventModalService', 'SelectAll', 'PrintingService', 'CurrentUser', CurrentHospsCtrl]);
