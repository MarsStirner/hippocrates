/**
 * Created by mmalkov on 24.09.14.
 */

'use strict';

var EventMeasureListCtrl = function ($scope, $q, RisarApi, TimeoutCallback, RefBookService) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;

    $scope.query = {};
    $scope.measure_list = [];
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
    };

    var selectMeasureTypes = function (on) {
        if (on) {
            $scope.query.measure_type = $scope.rbMeasureType.objects.clone();
        } else {
            $scope.query.measure_type = [];
        }
    };
    var selectMeasureStatuses = function (on) {
        if (on) {
            $scope.query.status = $scope.rbMeasureStatus.objects.clone();
        } else {
            $scope.query.status = [];
        }
    };
    var setMeasureData = function (data) {
        $scope.measure_list = data.measures;
        $scope.pager.pages = data.total_pages;
        $scope.pager.record_count = data.count;
    };
    var reloadChart = function () {
         return RisarApi.measure.get_chart(event_id).then(function (data) {
             $scope.header = data.header;
             setMeasureData(data.measures);
        });
    };
    var refreshMeasureList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var query = {
            page: $scope.pager.current_page,
            measure_type_id_list: $scope.query.measure_type.length ? _.pluck($scope.query.measure_type, 'id') : undefined,
            beg_date_from: $scope.query.beg_date_from ? moment($scope.query.beg_date_from).startOf('day').toDate() : undefined,
            beg_date_to: $scope.query.beg_date_to ? moment($scope.query.beg_date_to).endOf('day').toDate() : undefined,
            end_date_from: $scope.query.end_date_from ? moment($scope.query.end_date_from).startOf('day').toDate() : undefined,
            end_date_to: $scope.query.end_date_to ? moment($scope.query.end_date_to).endOf('day').toDate() : undefined,
            measure_status_id_list: $scope.query.status.length ? _.pluck($scope.query.status, 'id') : undefined
        };
        RisarApi.measure.get_by_event(event_id, query).then(setMeasureData);
    };
    var tc = new TimeoutCallback(refreshMeasureList, 600);

    $scope.resetFilters = function () {
        $scope.query = {
            measure_type: [],
            beg_date_from: null,
            beg_date_to: null,
            end_date_from: null,
            end_date_to: null,
            status: []
        };
    };
    $scope.onPageChanged = function () {
        refreshMeasureList(true);
    };
    $scope.init = function () {
        $scope.resetFilters();
        $scope.rbMeasureType = RefBookService.get('rbMeasureType');
        $scope.rbMeasureStatus = RefBookService.get('MeasureStatus');
        var chart_loading = reloadChart(event_id);
        $q.all([chart_loading, $scope.rbMeasureType.loading, $scope.rbMeasureStatus.loading]).
            then(function () {
                selectMeasureTypes(true);
                selectMeasureStatuses(true);
                $scope.$watchCollection('query', function (n, o) {
                    if (n !== o) tc.start();
                });
                $scope.$watchCollection('query.measure_type', function (n, o) {
                    if (n !== o) tc.start();
                });
                $scope.$watchCollection('query.status', function (n, o) {
                    if (n !== o) tc.start();
                });
            });
    };
    $scope.init();
};

WebMis20.controller('EventMeasureListCtrl', ['$scope', '$q', 'RisarApi', 'TimeoutCallback', 'RefBookService',
    EventMeasureListCtrl]);