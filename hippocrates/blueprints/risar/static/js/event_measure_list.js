'use strict';

var BaseMeasureListCtrl = function ($scope, EventMeasureService, EMModalService) {
    $scope.query = {};

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
    $scope.viewEventMeasure = function (idx) {
        var em = $scope.model.measure_list[idx];
        EMModalService.openView(em.data);
    };
    $scope.executeEm = function (idx) {
        var em = $scope.model.measure_list[idx];
        if ($scope.canExecuteEm(em)) {
            EventMeasureService.execute(em.data)
                .then(function (upd_em) {
                    $scope.model.measure_list.splice(idx, 1, upd_em);
                });
        }
    };
    $scope.cancelEm = function (idx) {
        var em = $scope.model.measure_list[idx];
        if ($scope.canCancelEm(em)) {
            EMModalService.openCancel(em.data).then(function (upd_em) {
                $scope.model.measure_list.splice(idx, 1, upd_em);
            });
        }
    };
    $scope.deleteEm = function (idx) {
        var em = $scope.model.measure_list[idx];
        EventMeasureService.del(em.data)
            .then(function (upd_em) {
                $scope.model.measure_list.splice(idx, 1, upd_em);
            });
    };
    $scope.restoreEm = function (idx) {
        var em = $scope.model.measure_list[idx];
        EventMeasureService.restore(em.data)
            .then(function (upd_em) {
                $scope.model.measure_list.splice(idx, 1, upd_em);
            });
    };
    $scope.openEmAppointment = function (idx) {
        var em = $scope.model.measure_list[idx];
        if ($scope.canReadEmAppointment(em)) {
            EventMeasureService.get_appointment(em)
                .then(function (appointment) {
                    return EMModalService.openAppointmentEdit(em, appointment);
                })
                .then(function (result) {
                    return EventMeasureService.get(em.data.id)
                        .then(function (upd_em) {
                            $scope.model.measure_list.splice(idx, 1, upd_em);
                        });
                });
        }
    };
    $scope.openEmResult = function (idx) {
        var em = $scope.model.measure_list[idx];
        if ($scope.canReadEmResult(em)) {
            EventMeasureService.get_em_result(em)
                .then(function (em_result) {
                    return EMModalService.openEmResultEdit(em, em_result);
                })
                .then(function (result) {
                    return EventMeasureService.get(em.data.id)
                        .then(function (upd_em) {
                            $scope.model.measure_list.splice(idx, 1, upd_em);
                        });
                });
        }
    };
    $scope.addNewEventMeasures = function () {
        return EMModalService.openCreate($scope.event_id, undefined, $scope.header.event)
            .then(function () {
                $scope.$broadcast('emDataUpdated');
            });
    };
    $scope.canReadEmAppointment = function (em) {
        return em.access.can_read_appointment;
    };
    $scope.canReadEmResult = function (em) {
        return em.access.can_read_result;
    };
    $scope.emHasAppointment = function (em) {
        return Boolean(em.data.appointment_action_id);
    };
    $scope.emHasResult = function (em) {
        return Boolean(em.data.result_action_id);
    };
    $scope.canDeleteEm = function (em) {
        return em.access.can_delete;
    };
    $scope.canRestoreEm = function (em) {
        return em.access.can_restore;
    };
    $scope.canExecuteEm = function (em) {
        return em.access.can_execute;
    };
    $scope.canCancelEm = function (em) {
        return em.access.can_cancel;
    };
    $scope.isManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 0;
    };
    $scope.isDeletedManualMeasure = function (em) {
        return !em.data.scheme && em.data.deleted === 1;
    };
};

var EventMeasureListCtrl = function ($scope, $controller, $q, RisarApi, RefBookService, PrintingService,
                                     PrintingDialog) {
    $controller('BaseMeasureListCtrl', {$scope: $scope});
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    var viewMode;
    $scope.model = {
        measure_list: [],
        checkups: []
    };
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };
    $scope.setViewMode = function (mode) {
        viewMode = mode;
        $scope.$broadcast('viewModeChanged', {
            mode: mode
        });
    };
    $scope.isTableMode = function () {
        return viewMode === 'table';
    };
    $scope.isCalendarMode = function () {
        return viewMode === 'calendar';
    };

    var reloadChart = function () {
        var header = RisarApi.chart.get_header($scope.event_id).then(function (data) {
            $scope.header = data.header;
        });
        var chart = RisarApi.measure.get_chart($scope.event_id).then(function (data) {
             $scope.chart = data;
        });
        return $q.all(header, chart);
    };

    $scope.resetFilters = function () {
        $scope.query = {
            checkups: [],
            measure_list: [],
            measure_type: [],
            beg_date_from: null,
            beg_date_to: null,
            end_date_from: null,
            end_date_to: null,
            status: []
        };
    };

    $scope.init = function () {
        $scope.resetFilters();
        $scope.rbMeasureType = RefBookService.get('rbMeasureType');
        $scope.rbMeasureStatus = RefBookService.get('MeasureStatus');
        var chart_loading = reloadChart($scope.event_id);
        $q.all([chart_loading, $scope.rbMeasureType.loading, $scope.rbMeasureStatus.loading]).
            then(function () {
                $scope.setViewMode('table');
            });
        RisarApi.measure.get_checkups($scope.event_id).then(function (data) {
             $scope.model.checkups = data.checkups;
        });
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()){
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
    };

    $scope.init();
};


var GynecolEventMeasureListCtrl = function ($scope, $controller, $q, RisarApi, RefBookService, PrintingService,
                                            PrintingDialog) {
    $controller('BaseMeasureListCtrl', {$scope: $scope});
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    var viewMode;
    $scope.model = {
        measure_list: [],
        checkups: []
    };
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };
    $scope.setViewMode = function (mode) {
        viewMode = mode;
        $scope.$broadcast('viewModeChanged', {
            mode: mode
        });
    };
    $scope.isTableMode = function () {
        return viewMode === 'table';
    };
    $scope.isCalendarMode = function () {
        return viewMode === 'calendar';
    };

    var reloadChart = function () {
        var header = RisarApi.chart.get_header($scope.event_id).then(function (data) {
            $scope.header = data.header;
        });
        var chart = RisarApi.measure.get_chart($scope.event_id).then(function (data) {
             $scope.chart = data;
        });
        return $q.all(header, chart);
    };

    $scope.resetFilters = function () {
        $scope.query = {
            checkups: [],
            measure_type: [],
            beg_date_from: null,
            beg_date_to: null,
            end_date_from: null,
            end_date_to: null,
            status: []
        };
    };

    $scope.init = function () {
        $scope.resetFilters();
        $scope.rbMeasureType = RefBookService.get('rbMeasureType');
        $scope.rbMeasureStatus = RefBookService.get('MeasureStatus');
        var chart_loading = reloadChart($scope.event_id);
        $q.all([chart_loading, $scope.rbMeasureType.loading, $scope.rbMeasureStatus.loading]).
            then(function () {
                $scope.setViewMode('table');
            });
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()){
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
    };

    $scope.init();
};


var EventMeasureTableViewCtrl = function ($scope, RisarApi, TimeoutCallback) {
    $scope.pager = {
        current_page: 1,
        max_pages: 10,
        pages: 1
    };

    var setMeasureData = function (data) {
        $scope.model.measure_list = data.measures;
        $scope.pager.pages = data.total_pages;
        $scope.pager.record_count = data.count;
    };
    var refreshMeasureList = function (set_page) {
        if (!set_page) {
            $scope.pager.current_page = 1;
        }
        var query = {
            page: $scope.pager.current_page,
            action_id_list: $scope.query.checkups.length ? _.pluck($scope.query.checkups, 'id') : undefined,
            measure_id_list: $scope.query.measure_list.length ? _.pluck($scope.query.measure_list, 'id') : undefined,
            measure_type_id_list: $scope.query.measure_type.length ? _.pluck($scope.query.measure_type, 'id') : undefined,
            beg_date_from: $scope.query.beg_date_from ? moment($scope.query.beg_date_from).startOf('day').toDate() : undefined,
            beg_date_to: $scope.query.beg_date_to ? moment($scope.query.beg_date_to).endOf('day').toDate() : undefined,
            end_date_from: $scope.query.end_date_from ? moment($scope.query.end_date_from).startOf('day').toDate() : undefined,
            end_date_to: $scope.query.end_date_to ? moment($scope.query.end_date_to).endOf('day').toDate() : undefined,
            measure_status_id_list: $scope.query.status.length ? _.pluck($scope.query.status, 'id') : undefined,
            with_deleted_hand_measures: true
        };
        RisarApi.measure.get_by_event($scope.event_id, query).then(setMeasureData);
    };
    var tc = new TimeoutCallback(refreshMeasureList, 600);

    $scope.onPageChanged = function () {
        refreshMeasureList(true);
    };

    var registered_watchers = [];
    $scope.$on('viewModeChanged', function (event, data) {
        var w_q, w_qmt, w_qs, w_qc;
        if (data.mode === 'table') {
            w_q = $scope.$watchCollection('query', function () { tc.start(); });
            w_qc = $scope.$watchCollection('query.checkups', function () { tc.start(); });
            w_qmt = $scope.$watchCollection('query.measure_type', function () { tc.start(); });
            w_qs = $scope.$watchCollection('query.status', function () { tc.start(); });
            registered_watchers.push(w_q);
            registered_watchers.push(w_qmt);
            registered_watchers.push(w_qs);
            registered_watchers.push(w_qc);
        } else {
            registered_watchers.forEach(function (unwatch) { unwatch(); });
            registered_watchers = [];
        }
    });
    $scope.$on('emDataUpdated', function () {
        refreshMeasureList(true);
    });
};

var EventMeasureCalendarViewCtrl = function ($scope, $timeout, RisarApi, TimeoutCallback, uiCalendarConfig) {
    function makeTask(el) {
        return {
            title: el.data.measure.name,
            start: el.data.beg_datetime,
            end: el.data.end_datetime,
            className: 'measure-status-' + el.data.status.code
        }
    }
    var refreshMeasureCalendar = function (start, end) {
        var query = {
            paginate: false,
            beg_date_to: end.local().endOf('day').toDate(),
            end_date_from: start.local().startOf('day').toDate(),
            measure_id_list: $scope.query.measure_list.length ? _.pluck($scope.query.measure_list, 'id') : undefined,
            action_id_list: $scope.query.checkups.length ? _.pluck($scope.query.checkups, 'id') : undefined,
            measure_type_id_list: $scope.query.measure_type.length ? _.pluck($scope.query.measure_type, 'id') : undefined,
            measure_status_id_list: $scope.query.status.length ? _.pluck($scope.query.status, 'id') : undefined,
            with_deleted_hand_measures: true
        };
        return RisarApi.measure.get_by_event($scope.event_id, query).
            then(function (measures) {
                return measures.map(makeTask);
            });
    };
    var firstRender = false;
    var reloadCalendar = function () {
        var event_type;
        if (!firstRender) {
            event_type = 'render';
            firstRender = true;
        } else {
            event_type = 'refetchEvents';
        }
        $timeout(function () {
            uiCalendarConfig.calendars.measureList.fullCalendar(event_type);
        });
    };
    $scope.measureLoader = function (start, end, timezone, callback) {
        refreshMeasureCalendar(start, end).then(function (tasks) {
            callback(tasks);
        });
    };
    $scope.eventSources = [
        $scope.measureLoader
    ];
    $scope.uiConfig = {
        calendar: {
            header: {
                left: 'month basicWeek basicDay',
                center: 'title',
                right: 'today prev,next'
            },
            lang: 'ru',
            timezone: 'local',
            height: 'auto',
            eventLimit: true
        }
    };
    var tc = new TimeoutCallback(function () {
        reloadCalendar();
    }, 600);

    var registered_watchers = [];
    $scope.$on('viewModeChanged', function (event, data) {
        var w_q, w_qmt, w_qs, w_qc;
        if (data.mode === 'calendar') {
            w_q = $scope.$watchCollection('query', function (n, o) {
                if (n !== o) tc.start();
            });
            w_qc = $scope.$watchCollection('query.checkups', function (n, o) {
                if (n !== o) tc.start();
            });
            w_qmt = $scope.$watchCollection('query.measure_type', function (n, o) {
                if (n !== o) tc.start();
            });
            w_qs = $scope.$watchCollection('query.status', function (n, o) {
                if (n !== o) tc.start();
            });
            registered_watchers.push(w_q);
            registered_watchers.push(w_qmt);
            registered_watchers.push(w_qs);
            registered_watchers.push(w_qc);
            if ($scope.chart.last_inspection_date) {
                uiCalendarConfig.calendars.measureList.fullCalendar('gotoDate', $scope.chart.last_inspection_date);
            }
            reloadCalendar();
        } else {
            registered_watchers.forEach(function (unwatch) { unwatch(); });
            registered_watchers = [];
        }
    });
    $scope.$on('emDataUpdated', function () {
        reloadCalendar();
    });
};

WebMis20.controller('BaseMeasureListCtrl', ['$scope', 'EventMeasureService', 'EMModalService',
    BaseMeasureListCtrl]);
WebMis20.controller('EventMeasureListCtrl', ['$scope', '$controller', '$q', 'RisarApi', 'RefBookService',
    'PrintingService', 'PrintingDialog', EventMeasureListCtrl]);
WebMis20.controller('GynecolEventMeasureListCtrl', ['$scope', '$controller', '$q', 'RisarApi', 'RefBookService',
    'PrintingService', 'PrintingDialog', GynecolEventMeasureListCtrl]);
WebMis20.controller('EventMeasureTableViewCtrl', ['$scope', 'RisarApi', 'TimeoutCallback',
    EventMeasureTableViewCtrl]);
WebMis20.controller('EventMeasureCalendarViewCtrl', ['$scope', '$timeout', 'RisarApi', 'TimeoutCallback',
    'uiCalendarConfig', EventMeasureCalendarViewCtrl]);