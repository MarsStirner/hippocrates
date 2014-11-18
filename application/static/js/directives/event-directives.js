'use strict';

angular.module('WebMis20.directives')
.directive('wmActionList', ['$window', 'ActionTypeTreeModal', 'MessageBox', 'WMEventServices', '$interval',
        function ($window, ActionTypeTreeModal, MessageBox, WMEventServices, $interval) {
    return {
        restrict: 'E',
        scope: {
            actions: '=',
            event: '=',
            actionTypeGroup: '@'
        },
        link: function (scope, element, attrs) {
            scope.can_delete_action = function (action) {
                return action.status.code !== 'finished' && action.can_delete;
            };
            scope.can_create_action = function () {
                return current_user.current_role_maybe('doctor', 'clinicDoctor', 'admin') && !scope.event.ro;
            };
            scope.open_action = function (action_id) {
                scope.child_window = $window.open(url_for_schedule_html_action + '?action_id=' + action_id);
            };

            scope.open_action_tree = function (at_class) {
                ActionTypeTreeModal.open(at_class, scope.event.event_id, scope.event.info.client.info)
                    .result.then(function (result) {
                        if(typeof (result) === 'object'){
                            scope.child_window = result;
                        } else {
                            scope.event.reload();
                        }
                    });
            };
            var interval;
            var clearInterval = function() {
                $interval.cancel(interval);
                interval = undefined;
            };
            scope.child_window = {};
            scope.$watch('child_window.document', function (n, o) {
                if (n && n!=o) {
                    clearInterval();
                    interval = $interval(function () {
                        if (scope.child_window.closed) {
                            scope.event.reload().then(function () {
                                scope.$root.$broadcast('event_loaded');
                            });
                            clearInterval();
                            scope.child_window = {};
                        }
                    }, 500);
                }
            });

            scope.delete_action = function (action) {
                MessageBox.question(
                    'Удаление записи',
                    'Вы уверены, что хотите удалить "{0}"?'.format(safe_traverse(action, ['name']))
                ).then(function () {
                    WMEventServices.delete_action(
                        scope.event, action
                    ).then(angular.noop, function () {
                        alert('Ошибка удаления действия. Свяжитесь с администратором.');
                    });
                });
            };
        },
        template:
'<table class="table table-condensed table-hover table-clickable">\
    <thead>\
    <tr>\
        <th>Тип действия</th>\
        <th>Состояние</th>\
        <th>Начало</th>\
        <th>Конец</th>\
        <th>Исполнитель</th>\
        <th></th>\
    </tr>\
    </thead>\
    <tbody>\
    <tr ng-repeat="action in actions | action_group_filter: actionTypeGroup" ng-class="{\'success\': action.status.code == \'finished\'}">\
        <td ng-click="open_action(action.id)">[[ action.name ]]</td>\
        <td ng-click="open_action(action.id)">[[action.status.name]]</td>\
        <td ng-click="open_action(action.id)">[[ action.begDate | asDate ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.endDate | asDateTime ]]</td>\
        <td ng-click="open_action(action.id)">[[ action.person_text ]]</td>\
        <td>\
            <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-show="can_delete_action(action)"\
                    ng-click="delete_action(action)"><span class="glyphicon glyphicon-trash"></span>\
            </button>\
        </td>\
    </tr>\
    <tr>\
        <td colspan="6">\
            <button type="button" class="btn btn-primary" ng-click="open_action_tree(actionTypeGroup)"\
                    ng-if="can_create_action()">Создать</button>\
        </td>\
    </tr>\
    </tbody>\
</table>'
    }
}]);