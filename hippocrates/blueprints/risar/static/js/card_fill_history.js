'use strict';

var CardFillHistoryCtrl = function ($scope, $q, $filter, RisarApi, RefBookService, PrintingService, PrintingDialog) {
    var params = aux.getQueryParams(window.location.search);
    var event_id = $scope.event_id = params.event_id;
    $scope.ps = new PrintingService("risar");
    $scope.ps.set_context("risar");
    $scope.ps_resolve = function () {
        return {
            event_id: $scope.event_id
        }
    };
    $scope.chart = {};

    var reloadChart = function () {
        var header = RisarApi.chart.get_header($scope.event_id).then(function (data) {
            $scope.header = data.header;
        });
        var chart = RisarApi.card_fill_rate.get_chart($scope.event_id).then(function (data) {
             $scope.chart = data;
        });
        return $q.all(header, chart);
    };

    $scope.init = function () {
        var chart_loading = reloadChart($scope.event_id);
        $q.all([chart_loading]);
    };

    $scope.open_print_window = function () {
        if ($scope.ps.is_available()){
            PrintingDialog.open($scope.ps, $scope.ps_resolve());
        }
    };

    $scope.get_document_info = function (item) {
        return '{0}{, |1}{, |2}'.formatNonEmpty(
            safe_traverse(item, ['document', 'name']),
            safe_traverse(item, ['document', 'set_person', 'name']),
            $filter('asDate')(safe_traverse(item, ['document', 'beg_date']))
        );
    };
    $scope.get_delay = function (item) {
        return item.delay_days || 'нет';
    };
    $scope.get_timeline_icon = function (fill_rate) {
        var code = fill_rate.code,
            icon_class = '';
        if (code === 'filled') icon_class = 'check bg-green';
        else if (code === 'not_filled') icon_class = 'times bg-red';
        else if (code === 'waiting') icon_class = 'hourglass-start bg-blue';
        return 'fa fa-{0}'.format(icon_class);
    };
    $scope.get_summary_icon = function (section) {
        var code = safe_traverse($scope.chart, ['card_fill_rates', 'card_fill_rate_' + section, 'code']),
            icon_class = '';
        if (code === 'filled') icon_class = 'check text-green';
        else if (code === 'not_filled') icon_class = 'times text-red';
        else if (code === 'waiting') icon_class = 'hourglass-start text-blue';
        return 'fa fa-{0}'.format(icon_class);
    };
    $scope.get_summary_tooltip = function (section) {
        var fill_rate = safe_traverse($scope.chart, ['card_fill_rates', 'card_fill_rate_' + section]);
        return $scope.get_icon_tooltip(fill_rate);
    };
    $scope.get_icon_tooltip = function (fill_rate) {
        if (!fill_rate) return '';
        return fill_rate.name;
    };
    $scope.summary_section_visible = function (section) {
        var code = safe_traverse($scope.chart, ['card_fill_rates', 'card_fill_rate_' + section, 'code']);
        return code !== 'not_required';
    };
    $scope.get_summary_cfr_text = function () {
        var code = safe_traverse($scope.chart, ['card_fill_rates', 'card_fill_rate', 'code']);
        if (!code) return 'Нет данных о заполненности карты';
        else if (code === 'filled') return 'Данные по пациентке заполнены полностью';
        else return 'Данные по пациентке заполнены не полностью';
    };

    $scope.init();
};

WebMis20.controller('CardFillHistoryCtrl', ['$scope', '$q', '$filter', 'RisarApi', 'RefBookService', 'PrintingService',
    'PrintingDialog', CardFillHistoryCtrl]);