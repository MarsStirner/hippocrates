/**
 * Created by mmalkov on 11.07.14.
 */
angular.module('WebMis20.services.dialogs', ['WebMis20.services', 'ui.bootstrap'])
.service('WMAppointmentDialog', function ($modal, WMAppointment) {
    return {
        cancel: function (ticket, person, client_id) {
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Отменить запись на приём?</h4>\
                    </div>\
                    <div class="modal-body" ng-if="!error">\
                        Отменить <span ng-if="ticket.attendance_type.code == \'CITO\'">экстренную</span>\
                        <span ng-if="ticket.attendance_type.code == \'extra\'">сверхплановую</span>\
                            запись на приём к [[ person.name ]] ([[ person.speciality.name ]])\
                        <span ng-if="ticket.attendance_type.code == \'planned\'">на [[ ticket.begDateTime | asMomentFormat:\'HH:mm DD MMM\' ]]</span>?\
                    </div>\
                    <div class="modal-body" ng-if="error">\
                        [[ error.text ]]\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-success" ng-click="accept()" ng-disabled="error">Ok</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Отмена</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.error = null;
                    $scope.accept = function () {
                        WMAppointment.cancel(ticket, client_id).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при отмене записи на приём'
                            }
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                }
            });
        },
        make: function (ticket, person, client_id) {
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Записать на приём?</h4>\
                    </div>\
                    <div class="modal-body">\
                        Записать на приём к [[ person.name ]] ([[ person.speciality.name ]])\
                        <span ng-if="ticket.attendance_type.code == \'planned\'">на [[ ticket.begDateTime | asMomentFormat:\'HH:mm DD MMM\' ]]</span>\
                        <span ng-if="ticket.attendance_type.code == \'CITO\'">экстренно</span>\
                        <span ng-if="ticket.attendance_type.code == \'extra\'">сверх плана</span>?\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-success" ng-click="accept()">Ok</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Отмена</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.accept = function () {
                        WMAppointment.make(ticket, client_id).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при записи на приём'
                            }
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                }
            });
        }
    }
});
