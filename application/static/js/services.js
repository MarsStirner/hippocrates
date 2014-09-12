'use strict';

angular.module('WebMis20.services', []).
    service('WMAppointment', ['$http', function ($http) {
        return {
            make: function (ticket, client_id) {
                var appointment_type_code = arguments[2];
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    appointment_type_code: appointment_type_code // Это может настраиваться
                })
            },
            cancel: function (ticket, client_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    delete: true
                })
            },
            change_notes: function (ticket_client_id, notes) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    note: notes
                })
            }
        }
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