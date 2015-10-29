'use strict';

WebMis20.service('EMModalService', ['$modal', function ($modal) {
    return {
        openView: function (event_measure) {
            var instance = $modal.open({
                templateUrl: '/WebMis20/RISAR/modal/event_measure_view.html',
                controller: EventMeasureModalCtrl,
                //backdrop: 'static',
                //size: 'lg',
                resolve: {
                    event_measure: function () {
                        return event_measure;
                    }
                }
            });
            return instance.result;
        },
        openEdit: function () {

        }
    }
}]);

WebMis20.service('EventMeasureService', ['RisarApi', function (RisarApi) {
    this.cancel = function (em) {
        return RisarApi.measure.cancel(em.id);
    };
    this.make_direction = function (em) {
        return RisarApi.measure.make_direction(em.id);
    };
}]);

WebMis20.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/RISAR/modal/event_measure_view.html',
        '\
<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title">Просмотр информации о мероприятии</h4>\
</div>\
<div class="modal-body">\
    <form class="form-horizontal">\
        <div class="form-group">\
            <label for="measure_type" class="col-sm-3 control-label">Схема</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_type" ng-bind="getSchemeInfo()"></span>\
            </div>\
        </div>\
        <hr>\
        <div class="form-group">\
            <label for="measure_type" class="col-sm-3 control-label">Тип мероприятия</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_type" ng-bind="event_measure.scheme_measure.measure.measure_type.name"></span>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure" class="col-sm-3 control-label">Мероприятие</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure" ng-bind="event_measure.scheme_measure.measure.name"></span>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_status" class="col-sm-3 control-label">Статус</label>\
            <div class="col-sm-9 form-control-static">\
                <event-measure-status id="measure_status" status="event_measure.status"></event-measure-status>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_dates" class="col-sm-3 control-label">Период выполнения</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_dates" ng-bind="getMeasureDateRange()"></span>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_dates" class="col-sm-3 control-label">Документы</label>\
            <div class="col-sm-9 form-control-static">\
                Направление: [[ getDirectionInfo() ]]\
            </div>\
            <div class="col-sm-offset-3 col-sm-9 form-control-static">\
                Результат: -\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_exec_date" class="col-sm-3 control-label">Дата выполнения</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_exec_date">-</span>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_create" class="col-sm-3 control-label">Создано</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_create" ng-bind="getMeasureCreateInfo()"></span>\
            </div>\
        </div>\
        <div class="form-group">\
            <label for="measure_modify" class="col-sm-3 control-label">Изменено</label>\
            <div class="col-sm-9 form-control-static">\
                <span id="measure_modify" ng-bind="getMeasureModifyInfo()"></span>\
            </div>\
        </div>\
    </form>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Закрыть</button>\
</div>');
}]);


var EventMeasureModalCtrl = function ($scope, $filter, RisarApi, RefBookService, event_measure) {
    $scope.event_measure = event_measure;

    $scope.getSchemeInfo = function () {
        return '{0}. {1}'.format(event_measure.scheme_measure.scheme.number, event_measure.scheme_measure.scheme.name);
    };
    $scope.getMeasureDateRange = function () {
        return '{0} - {1}'.format(
            $filter('asDateTime')(event_measure.beg_datetime),
            $filter('asDateTime')(event_measure.end_datetime)
        );
    };
    $scope.getMeasureCreateInfo = function () {
        return '{0}, {1}'.format(
            $filter('asDateTime')(event_measure.create_datetime),
            safe_traverse(event_measure, ['create_person', 'short_name'])
        );
    };
    $scope.getMeasureModifyInfo = function () {
        return '{0}, {1}'.format(
            $filter('asDateTime')(event_measure.modify_datetime),
            safe_traverse(event_measure, ['modify_person', 'short_name'])
        );
    };
    $scope.getDirectionInfo = function () {
        return '{0}'.format(
            event_measure.action_id || ' - '
        );
    };
    $scope.init = function () {

    };

    $scope.init();
};


WebMis20.controller('EventMeasureModalCtrl', ['$scope', 'RisarApi', 'RefBookService',
    EventMeasureModalCtrl]);


WebMis20.directive('eventMeasureStatus', [function () {
    return {
        restrict: 'E',
        scope: {
            status: '='
        },
        template:
'<span class="label" ng-class="getClass()">[[ status.name ]]</span>',
        link: function (scope, elem, attrs) {
            scope.getClass = function () {
                var text = 'measure-status-{0}'.format(scope.status.code);
                return text;
            };
        }
    }
}]);