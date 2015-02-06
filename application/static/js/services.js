'use strict';

angular.module('WebMis20.services', []).
    service('WMAppointment', ['$http', function ($http) {
        return {
            make: function (ticket, client_id, appointment_type_id, associated_event_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    appointment_type_id: appointment_type_id,
                    event_id: associated_event_id
                });
            },
            cancel: function (ticket, client_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    delete: true
                });
            },
            change_notes: function (ticket_client_id, notes) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    note: notes
                });
            }
        }
    }]).
    service('AgeSex', [function() {
        return {
            sex_acceptable: function (client, sex) {
                return ! (sex && sex !== client.sex_raw);
            },
            age_acceptable: function (client, selector) {
                return ! (
                    selector[0] != 0 && client.age_tuple[selector[0] - 1] < selector[1] ||
                    selector[2] != 0 && client.age_tuple[selector[2] - 1] > selector[3]
                );
            }
        }
    }]).
    service('WMWindowSync', ['$window', '$rootScope', '$interval', function ($window, $rootScope, $interval) {
        return {
            openTab: function (url, onCloseCallback) {
                var interval,
                    clearInterval = function() {
                        $interval.cancel(interval);
                        interval = undefined;
                    };
                var w = $window.open(url);
                interval = $interval(function () {
                    if (w.closed) {
                        (onCloseCallback || angular.noop)();
                        clearInterval();
                        w = undefined;
                    }
                }, 500);
            }
        }
    }]).
    service('CurrentUser', [function () {
        // пока инициализация через глобального юзера, а потом через rest
        angular.extend(this, current_user);
        this.get_main_user = function () {
            return this.master || this;
        };
        this.has_right = function () {
            return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
        };
        this.has_role = function () {
            return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
        };
        this.current_role_in = function () {
            return [].clone.call(arguments).has(this.current_role);
        };
    }]).
    service('IdleUserModal', ['$modal', 'Idle', function ($modal, Idle) {
        return {
            open: function () {
                var IUController = function ($scope) {
                    $scope.countdown = Idle._options().timeout;
                    $scope.idletime_min = Math.floor(Idle._options().idle / 60) || 1;
                    $scope.$on('IdleWarn', function(e, countdown) {
                        $scope.countdown = countdown;
                    });
                    $scope.$on('IdleTimeout', function() {
                        $scope.countdown = 0;
                        $scope.$dismiss('Так и не вернулся...');
                    });
                    $scope.cancel_idle = function () {
                        $scope.$close('Успел!');
                    };
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-IdleUser.html',
                    controller: IUController,
                    backdrop: 'static',
                    windowClass: 'idle-modal'
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-IdleUser.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <h3 class="modal-title">Внимание!</h3>\
            </div>\
            <div class="modal-body">\
                <div>\
                  <p>Вы неактивны более <b>[[idletime_min]]</b> минут.<br>\
                    Автоматический выход из системы произойдет через:</p>\
                    <h1 class="idle-countdown"><span class="label label-danger">[[countdown]]</span><small> секунд</small></h1>\
                </div>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success btn-lg" ng-click="cancel_idle()">Остаться в системе</button>\
            </div>'
        );
    }]).
    service('MessageBox', ['$modal', function ($modal) {
        return {
            info: function (head, message) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.message = message;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-info.html',
                    controller: MBController
                });
                return instance.result;
            },
            error: function (head, message) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.message = message;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-error.html',
                    controller: MBController
                });
                return instance.result;
            },
            question: function (head, question) {
                var MBController = function ($scope) {
                    $scope.head_msg = head;
                    $scope.question = question;
                };
                var instance = $modal.open({
                    templateUrl: '/WebMis20/modal-MessageBox-question.html',
                    controller: MBController
                });
                return instance.result;
            }
        };
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-info.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="message"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
            </div>'
        );
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-error.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="message"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
            </div>'
        );
    }]).
    run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-MessageBox-question.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title">[[head_msg]]</h4>\
            </div>\
            <div class="modal-body">\
                <p ng-bind-html="question"></p>\
            </div>\
            <div class="modal-footer">\
                <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
                <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            </div>'
        );
    }]);